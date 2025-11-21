from Bots.bot_ai import BotAI
from Bots.my_ai import MyAI
from Bots.stayinalign_ai import StayinAlignAI

ai_bots = {
    "MyAI": MyAI,
    "StayinAlignAI": StayinAlignAI,
}


def ai_factory(bot_selection="MyAI") -> BotAI:
    return ai_bots[bot_selection]()
