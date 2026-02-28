using Duohabbit.Core.Enums;

namespace Duohabbit.Core.Entities;

public class HabitPeriod
{
    public Guid Id { get; set; }
    public Guid HabitId { get; set; }
    public string PeriodKey { get; set; } = string.Empty; // YYYY-MM-DD
    public PeriodStatus Status { get; set; }
    public DateTime CalculatedAt { get; set; }

    // Navigation properties
    public Habit Habit { get; set; } = null!;
}