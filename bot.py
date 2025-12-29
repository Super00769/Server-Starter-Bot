import discord
import requests
import os
from threading import Thread
from flask import Flask

# ==========================================
# 🔐 CONFIGURATION (LOADS FROM CLOUD SECRETS)
# ==========================================
# Render will provide these secrets automatically
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = os.environ.get('REPO_OWNER', "Super00769")
REPO_NAME = os.environ.get('REPO_NAME', "RDP")
WORKFLOW_FILE = "RDP.yml" 

# Role ID (Safety Check)
try:
    ALLOWED_ROLE_ID = int(os.environ.get('ALLOWED_ROLE_ID', "0"))
except:
    ALLOWED_ROLE_ID = 0

# ==========================================

processing_command = False
app = Flask('')

@app.route('/')
def home():
    return "I am alive! The bot is running."

def run():
    # Render assigns a random port, we must use it
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- THE BOT LOGIC ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def is_server_already_running():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_FILE}/runs"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    params = {"status": "in_progress"} 
    try:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        return r.json().get("total_count", 0) > 0
    except:
        return False

@client.event
async def on_ready():
    print(f'✅ Bot is Online on Render! Logged in as {client.user}')

@client.event
async def on_message(message):
    global processing_command
    if message.author == client.user: return

    if message.content.lower() == '!start':
        
        # Permission Check
        if ALLOWED_ROLE_ID != 0:
            user_roles = [role.id for role in message.author.roles]
            if ALLOWED_ROLE_ID not in user_roles:
                await message.channel.send("⛔ **Access Denied.**")
                return

        if processing_command:
            await message.channel.send("⏳ **Hold on!** Working on it...")
            return
        
        processing_command = True 
        
        try:
            await message.channel.send("📡 **Connecting to Headquarters...**")
            
            if is_server_already_running():
                await message.channel.send("⚠️ **System Online:** Server is already running.")
                processing_command = False
                return

            await message.channel.send("🚀 **Authorized!** Sending launch codes...")
            
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_FILE}/dispatches"
            data = {"ref": "main"}
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 204:
                await message.channel.send("✅ **Deploying!** Ready in 3-5 minutes.")
            else:
                await message.channel.send(f"❌ **Failed:** {response.status_code}")
        
        except Exception as e:
            await message.channel.send(f"❌ **Error:** {e}")
        
        processing_command = False

if __name__ == '__main__':
    keep_alive()
    client.run(DISCORD_TOKEN)
