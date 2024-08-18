class Run:
    def __init__(self, link, user_names, time, category_name, game_id, run_id, game_name):
        self.link = link
        self.user_names = user_names
        self.time = time
        self.category_name = category_name
        self.game_name = game_name
        self.game_id = game_id
        self.run_id = run_id

    def __eq__(self, other):
        if other is None:
            return False
        return self.link == other.link

    def __ne__(self, other):
        return not self.__eq__(other)

    if __name__ == "__main__":
    # Import the bot.py script
        import bot
