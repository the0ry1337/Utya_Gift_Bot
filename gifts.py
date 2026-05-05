from dataclasses import dataclass


@dataclass(frozen=True)
class Gift:
    emoji: str
    collection: str
    model: str

    @property
    def display_name(self) -> str:
        return f"{self.emoji} {self.collection} — {self.model}"

    @property
    def getgems_slug(self) -> str:
        return self.collection.lower().replace(" ", "-").replace("'", "")

    @property
    def fragment_slug(self) -> str:
        return self.collection.lower().replace(" ", "-").replace("'", "")


GIFTS: list[Gift] = [
    Gift("🛁", "Artisan Brick", "Duck Bath"),
    Gift("⌨️", "Input Key", "Utya"),
    Gift("🎁", "Loot Bag", "Riot Pack"),
    Gift("📎", "Nail Bracelet", "Duck Amulet"),
    Gift("🎁", "Love Potion", "Durov Duck"),
    Gift("🎁", "Bonded Ring", "Duckling"),
    Gift("🎁", "Snow Globe", "Cherry Duck"),
    Gift("🍲", "Hex Pot", "Bubble Bath"),
    Gift("🎁", "Signet Ring", "Utya"),
    Gift("🍫", "Valentine Box", "Pizza"),
    Gift("🎁", "Snow Globe", "House of Cards"),
    Gift("🌺", "Skull Flower", "Joyful Duck"),
    Gift("🕯", "B-Day Candle", "Attack"),
    Gift("❤️", "Restless Jar", "Utya Duck"),
    Gift("🗃", "Joyful Bundle", "Pool Party"),
    Gift("🎀", "Bow Tie", "Utyan"),
    Gift("🎁", "Jack-in-the-Box", "Amogus"),
    Gift("🧁", "Whip Cupcake", "Sponge Duck"),
    Gift("🚘", "Low Rider", "Sticker Gang"),
    Gift("🎩", "Top Hat", "Pixel Perfect"),
    Gift("🌹", "Eternal Rose", "Vivid Prize"),
    Gift("🚀", "Stellar Rocket", "To The Moon"),
    Gift("🍦", "Ice Cream", "Utya Pop"),
    Gift("🐰", "Easter Basket", "Claw Machine"),
]
