using Duohabbit.Core.Enums;

namespace Duohabbit.Core.Entities;

public class Habit
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public Guid OwnerId { get; set; }
    public string Schedule { get; set; } = "daily"; // daily, weekly, etc.
    public TimeSpan Deadline { get; set; } // Local deadline time
    public DateTime CreatedAt { get; set; }
    public bool IsActive { get; set; }

    // Navigation properties
    public ICollection<HabitParticipant> Participants { get; set; } = new List<HabitParticipant>();
    public ICollection<HabitPeriod> Periods { get; set; } = new List<HabitPeriod>();
}