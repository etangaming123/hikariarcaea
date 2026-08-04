import discord
from discord.ext import commands
from discord import app_commands

from common import etanid


# say commands
class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="wonder what this does")
    @app_commands.describe(message="The message to send in the channel.")
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.id == etanid:
            await interaction.edit_original_response(content=f"You do not have permission to use this command.")
            return
        await interaction.channel.send(message)
        await interaction.edit_original_response(content=f"Done!")

    @app_commands.command(name="say-dm", description="wonder what this does but in dms")
    @app_commands.describe(user="The user to send the DM to.", message="The message to send.")
    async def say_dm(self, interaction: discord.Interaction, user: discord.User, message: str):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.id == etanid:
            await interaction.edit_original_response(content=f"You do not have permission to use this command.")
            return
        try:
            dm = await user.create_dm()
            await dm.send(message)
        except discord.Forbidden:
            await interaction.edit_original_response(content=f"Failed to send DM. The user might have DMs disabled.")
            return
        await interaction.edit_original_response(content=f"Done!")

    @app_commands.command(name="say-form", description="same as /say but with a form, so you can multiline")
    async def say_form(self, interaction: discord.Interaction):
        if not interaction.user.id == etanid:
            await interaction.response.send_message(content=f"You do not have permission to use this command.", ephemeral=True)
            return

        class SayModal(discord.ui.Modal, title="Say Command"):
            message = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph)

            async def on_submit(self, interaction: discord.Interaction):
                await interaction.channel.send(self.message.value)
                await interaction.response.send_message(content=f"Done!", ephemeral=True)

        await interaction.response.send_modal(SayModal())


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
