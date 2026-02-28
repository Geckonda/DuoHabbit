namespace Duohabbit.Core.Entities;

public class HabitParticipant
{
    public Guid Id { get; set; }
    public Guid HabitId { get; set; }
    public Guid UserId { get; set; }
    public DateTime JoinedAt { get; set; }
    public bool IsActive { get; set; }

    // Navigation properties
    public Habit Habit { get; set; } = null!;
    public ICollection<Completion> Completions { get; set; } = new List<Completion>();
}