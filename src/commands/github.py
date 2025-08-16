"""GitHub integration commands."""
import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger
from typing import Optional
from src.integrations.github import operations


class GitHubCommands(commands.Cog):
    """GitHub integration commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="github-prs", description="List open pull requests")
    @app_commands.describe(repo="Repository name (e.g., org/repo)")
    async def github_prs(self, interaction: discord.Interaction, repo: str) -> None:
        """List open pull requests for a given repo."""
        await interaction.response.defer()
        try:
            prs = await operations.list_pull_requests(repo)
            embed = discord.Embed(title=f"📋 Open PRs in {repo}", color=discord.Color.purple())
            if not prs:
                embed.description = "No open pull requests."
            else:
                for pr in prs:
                    embed.add_field(
                        name=pr["title"],
                        value=f"[#{pr['number']}]({pr['url']}) by {pr['user']}",
                        inline=False
                    )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error fetching PRs: {e}")
            await interaction.followup.send("❌ Failed to fetch pull requests.")

    @app_commands.command(name="github-issues", description="List open issues")
    @app_commands.describe(repo="Repository name (e.g., org/repo)")
    async def github_issues(self, interaction: discord.Interaction, repo: str) -> None:
        """List open issues for a given repo."""
        await interaction.response.defer()
        try:
            issues = await operations.list_issues(repo)
            embed = discord.Embed(title=f"🐞 Open Issues in {repo}", color=discord.Color.red())
            if not issues:
                embed.description = "No open issues."
            else:
                for issue in issues:
                    embed.add_field(
                        name=issue["title"],
                        value=f"[#{issue['number']}]({issue['url']}) by {issue['user']}",
                        inline=False
                    )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            await interaction.followup.send("❌ Failed to fetch issues.")

    @app_commands.command(name="github-repos", description="List tracked repositories")
    async def github_repos(self, interaction: discord.Interaction) -> None:
        """List all repos this bot is tracking."""
        await interaction.response.defer()
        try:
            repos = await operations.list_tracked_repositories()
            embed = discord.Embed(title="📁 Tracked Repositories", color=discord.Color.blue())
            if not repos:
                embed.description = "No repositories are being tracked yet."
            else:
                embed.description = "\n".join(f"• `{r}`" for r in repos)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error listing repos: {e}")
            await interaction.followup.send("❌ Failed to list repositories.")

    @app_commands.command(name="github-subscribe", description="Subscribe this channel to a repository's events")
    @app_commands.describe(repo="Repository name (e.g., org/repo)", channel="Target channel")
    async def github_subscribe(
        self,
        interaction: discord.Interaction,
        repo: str,
        channel: discord.TextChannel
    ) -> None:
        """Subscribe a Discord channel to GitHub events."""
        await interaction.response.defer()
        try:
            await operations.subscribe_channel(repo, channel.id)
            await interaction.followup.send(f"✅ Subscribed {channel.mention} to `{repo}` events.")
        except Exception as e:
            logger.error(f"Error subscribing to repo: {e}")
            await interaction.followup.send("❌ Failed to subscribe to repository.")

    @app_commands.command(name="github-unsubscribe", description="Unsubscribe this channel from a repository's events")
    @app_commands.describe(repo="Repository name (e.g., org/repo)", channel="Target channel")
    async def github_unsubscribe(
        self,
        interaction: discord.Interaction,
        repo: str,
        channel: discord.TextChannel
    ) -> None:
        """Unsubscribe a Discord channel from GitHub events."""
        await interaction.response.defer()
        try:
            await operations.unsubscribe_channel(repo, channel.id)
            await interaction.followup.send(f"✅ Unsubscribed {channel.mention} from `{repo}` events.")
        except Exception as e:
            logger.error(f"Error unsubscribing from repo: {e}")
            await interaction.followup.send("❌ Failed to unsubscribe from repository.")


async def setup(bot: commands.Bot) -> None:
    """Setup function to add cog to bot."""
    await bot.add_cog(GitHubCommands(bot))

