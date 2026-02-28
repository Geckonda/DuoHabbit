FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src

# Копируем файлы проектов
COPY ["src/Duohabbit.API/Duohabbit.API.csproj", "Duohabbit.API/"]
COPY ["src/Duohabbit.Core/Duohabbit.Core.csproj", "Duohabbit.Core/"]
COPY ["src/Duohabbit.Infrastructure/Duohabbit.Infrastructure.csproj", "Duohabbit.Infrastructure/"]
COPY ["src/Duohabbit.Hubs/Duohabbit.Hubs.csproj", "Duohabbit.Hubs/"]

# Восстанавливаем зависимости
RUN dotnet restore "Duohabbit.API/Duohabbit.API.csproj"

# Копируем весь код
COPY src/ .

# Публикуем приложение
WORKDIR "/src/Duohabbit.API"
RUN dotnet publish -c Release -o /app/publish

# Финальный образ
FROM mcr.microsoft.com/dotnet/aspnet:9.0
WORKDIR /app
COPY --from=build /app/publish .


# ENV ASPNETCORE_ENVIRONMENT=Development


ENTRYPOINT ["dotnet", "Duohabbit.API.dll"]