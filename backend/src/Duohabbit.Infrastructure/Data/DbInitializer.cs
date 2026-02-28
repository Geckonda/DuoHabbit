using Microsoft.EntityFrameworkCore;
using Duohabbit.Core.Entities;

namespace Duohabbit.Infrastructure.Data;

public static class DbInitializer
{
    public static void Initialize(ApplicationDbContext context)
    {
        context.Database.Migrate();

        // Добавляем тестовые данные только если БД пустая
        if (!context.Habits.Any())
        {
            var habitId = Guid.NewGuid();

            var testHabit = new Habit
            {
                Id = habitId,
                Title = "Утренняя пробежка",
                Description = "Пробежать 3 км в парке",
                OwnerId = Guid.NewGuid(), // В реальности ID пользователя
                Schedule = "daily",
                Deadline = new TimeSpan(10, 0, 0), // 10:00 утра
                CreatedAt = DateTime.UtcNow,
                IsActive = true
            };

            context.Habits.Add(testHabit);
            context.SaveChanges();

            Console.WriteLine("Test data seeded successfully!");
        }
    }
}