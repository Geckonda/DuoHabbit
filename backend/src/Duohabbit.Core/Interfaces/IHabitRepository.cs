using Duohabbit.Core.Entities;

namespace Duohabbit.Core.Interfaces;

public interface IHabitRepository
{
    Task<Habit?> GetByIdAsync(Guid id);
    Task<IEnumerable<Habit>> GetUserHabitsAsync(Guid userId);
    Task<Habit> CreateAsync(Habit habit);
    Task UpdateAsync(Habit habit);
    Task DeleteAsync(Guid id);
    Task<bool> ExistsAsync(Guid id);
}