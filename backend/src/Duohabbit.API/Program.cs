using Duohabbit.Hubs.Hubs;
using Duohabbit.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using System.Reflection;

var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Add SignalR
builder.Services.AddSignalR();

// Add Database
// Добавляем более надежное подключение к БД
builder.Services.AddDbContext<ApplicationDbContext>((serviceProvider, options) =>
{
    var connectionString = Environment.GetEnvironmentVariable("ConnectionStrings__DefaultConnection")
                          ?? builder.Configuration.GetConnectionString("DefaultConnection");

    Console.WriteLine("CS: " + connectionString);

    // Логируем попытки подключения в Development
    if (builder.Environment.IsDevelopment())
    {
        options.UseNpgsql(connectionString, npgsqlOptions =>
        {
            npgsqlOptions.EnableRetryOnFailure(
                maxRetryCount: 5,
                maxRetryDelay: TimeSpan.FromSeconds(10),
                errorCodesToAdd: null);
        });
        options.EnableSensitiveDataLogging();
        options.EnableDetailedErrors();
    }
    else
    {
        options.UseNpgsql(connectionString);
    }
});


// Add CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("VueApp", policy =>
    {
        policy.WithOrigins("http://localhost:3000")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

var app = builder.Build();

// Добавляем автоматическое применение миграций при старте
if (builder.Environment.IsDevelopment())
{
    using var scope = app.Services.CreateScope();
    var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

    // Ждем готовности PostgreSQL (до 30 секунд)
    for (int i = 0; i < 6; i++)
    {
        try
        {
            if (dbContext.Database.CanConnect())
            {
                dbContext.Database.Migrate(); // Применяем миграции
                Console.WriteLine("Database connected and migrations applied successfully!");
                break;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Attempt {i + 1}: Database not ready. Retrying in 5 seconds...");
            Console.WriteLine($"Error: {ex.Message}");
            Thread.Sleep(5000);
        }
    }

    Console.WriteLine("[Builder]У нас Dev");
}
else
{
    Console.WriteLine("[Builder]У нас PROD");
}
// Configure pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
    Console.WriteLine("[App]У нас dev");
}
else
{
    Console.WriteLine("У нас PROD");
}

app.UseHttpsRedirection();
app.UseCors("VueApp");
app.UseAuthorization();
app.MapControllers();
app.MapHub<HabitHub>("/hubs/habit");

app.Run();