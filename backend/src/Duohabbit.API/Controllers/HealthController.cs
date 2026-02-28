using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Duohabbit.Infrastructure.Data;

namespace Duohabbit.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class HealthController : ControllerBase
{
    private readonly ApplicationDbContext _db;

    public HealthController(ApplicationDbContext db)
    {
        _db = db;
    }

    [HttpGet("hw")]
    public async Task<IActionResult> HelloWorld()
    {
        return Ok("Hello wrold!");
    }
    [HttpGet("db")]
    public async Task<IActionResult> CheckDatabase()
    {
        try
        {
            var canConnect = await _db.Database.CanConnectAsync();
            if (canConnect)
            {
                // Пробуем выполнить простой запрос
                var count = await _db.Habits.CountAsync();
                return Ok(new
                {
                    status = "Connected to database",
                    habitCount = count,
                    database = "PostgreSQL in Docker"
                });
            }
            return StatusCode(500, "Cannot connect to database");
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { error = ex.Message });
        }
    }
}