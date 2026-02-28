namespace Duohabbit.Core.Entities;

public class Completion
{
    public Guid Id { get; set; }
    public Guid HabitParticipantId { get; set; }
    public string PeriodKey { get; set; } = string.Empty; // YYYY-MM-DD
    public DateTime CompletedAt { get; set; }
    public bool IsUndone { get; set; }

    // Navigation properties
    public HabitParticipant Participant { get; set; } = null!;
}