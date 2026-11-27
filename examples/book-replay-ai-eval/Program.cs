using System.Diagnostics;
using System.Text.Json;

if (args is not [var python, var destination] || !File.Exists(python) ||
    File.Exists(destination) || Directory.Exists(destination))
    throw new ArgumentException("Supply the path to Python and a new output directory.");

Directory.CreateDirectory(destination);
var arms = await Task.WhenAll(new[] { "fixed", "random", "ai" }.Select(Observe));
foreach (var arm in arms)
    Console.WriteLine(arm switch
    {
        Completed completed => $"{completed.Name}: {completed.Report.GetProperty("executions")} observed executions",
        Failed failed => $"{failed.Name}: infrastructure/protocol error: {failed.Reason}",
        Expired expired => $"{expired.Name}: worker deadline expired",
    });

if (arms.OfType<Completed>().Count() != arms.Length)
    return 1;

var summaries = arms.Cast<Completed>().ToDictionary(a => a.Name, a => a.Report);
var fixedArm = summaries["fixed"];
var randomArm = summaries["random"];
var aiArm = summaries["ai"];
foreach (var arm in summaries.Values)
{
    if (arm.GetProperty("submitted").GetInt32() != 72 || arm.GetProperty("executions").GetInt32() != 288 ||
        arm.GetProperty("invalid").GetInt32() != 0 || arm.GetProperty("original_runs").GetInt32() != 72 ||
        arm.GetProperty("outcomes").TryGetProperty("HARNESS_ERROR", out _))
        throw new InvalidDataException("Local matched execution did not complete.");
}

var baselineFailures = Identities(fixedArm).Union(Identities(randomArm));
var baselinePairs = Pairs(fixedArm).Union(Pairs(randomArm));
var extraSignatures = Identities(aiArm).Except(baselineFailures).Order().ToArray();
var extraPairs = Pairs(aiArm).Except(baselinePairs).Order().ToArray();
var evidence = new
{
    runtime = Environment.Version.ToString(),
    arms = summaries,
    extraFailureSignatures = extraSignatures,
    extraScenarioPairs = extraPairs
};
await File.WriteAllTextAsync(Path.Combine(destination, "comparison.json"),
    JsonSerializer.Serialize(evidence, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"New AI signatures: {extraSignatures.Length}; new AI scenario pairs: {extraPairs.Length}");
return 0;

async Task<WorkerOutcome> Observe(string arm)
{
    var start = new ProcessStartInfo(python)
    {
        UseShellExecute = false,
        RedirectStandardOutput = true,
        RedirectStandardError = true
    };
    foreach (var argument in new[] { "-B", Path.GetFullPath("evaluate.py"), arm, Path.Combine(destination, arm) })
        start.ArgumentList.Add(argument);
    using var cutoff = new CancellationTokenSource(TimeSpan.FromMinutes(4));
    try
    {
        var output = await Process.RunAndCaptureTextAsync(start, cutoff.Token);
        if (output.ExitStatus.ExitCode != 0)
            return new Failed(arm, output.StandardError.Trim());
        using var json = JsonDocument.Parse(output.StandardOutput);
        var result = json.RootElement;
        if (result.GetProperty("schema").GetString() != "local-book-replay-arm/1" ||
            result.GetProperty("arm").GetString() != arm)
            return new Failed(arm, "Result did not bind to the requested arm.");
        return new Completed(arm, result.Clone());
    }
    catch (OperationCanceledException) when (cutoff.IsCancellationRequested)
    {
        return new Expired(arm);
    }
    catch (Exception issue) when (issue is JsonException or KeyNotFoundException or InvalidOperationException)
    {
        return new Failed(arm, issue.Message);
    }
}

static IEnumerable<string> Identities(JsonElement arm) =>
    arm.GetProperty("failure_identities").EnumerateArray().Select(x => x.GetString()!);

static IEnumerable<string> Pairs(JsonElement arm) =>
    arm.GetProperty("adjacent_pair_witnesses").EnumerateObject().Select(x => x.Name);

closed record WorkerOutcome(string Name);
sealed record Completed(string Arm, JsonElement Report) : WorkerOutcome(Arm);
sealed record Failed(string Arm, string Reason) : WorkerOutcome(Arm);
sealed record Expired(string Arm) : WorkerOutcome(Arm);
