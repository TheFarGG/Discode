from typing import List

from .channel import TextChannel


class Guild:
    def __init__(self, data: dict, loop, http):
        self.http = http
        self.loop = loop
        self.data = data
        self.icon = data.get("icon")
        self.splash = data.get("splash")
        self.discovery_splash: data.get("discovery_splash")
        self.emojis = data.get("emojis")
        self.description = data.get("description")
        self.owner_id = data.get("owner_id")
        self.region = data.get("region")
        self.afk_channel_id = data.get("afk_channel_id")
        self.afk_timeout = data.get("afk_timeout")
        self.default_message_notifications = data.get("default_message_notifications")
        self.explicit_content_filter = data.get("explicit_content_filter")
        self.roles = data.get("roles")
        self.rules_channel_id = data.get("rules_channel_id")
        self.vanity_url_code = data.get("vanity_url_code")
        self.banner = data.get("banner")
        self.premium_tier = data.get("premium_tier")

    @property
    def name(self) -> str:
        return self.data.get("name")

    @property
    def id(self) -> int:
        return int(self.data.get("id"))

    @property
    def mfa_level(self) -> int:
        return self.data.get("mfa_level")

    @property
    def verification_level(self) -> int:
        return self.data.get("verification_level")

    @property
    def nsfw_level(self) -> int:
        return self.data.get("nsfw_level")

    @property
    def features(self) -> list:
        data_features = self.data.get("features")
        if not data_features:
            return data_features
        else:
            new_features = []
            for feature in data_features:
                new_features.append(feature.lower())
            return new_features

    @property
    def channels(self) -> List:
        if getattr(self, "_channels", None):
            return self._channels

        self._channels = []
        for ch in self.data.get("channels"):
            ch["http"] = self.http
            if ch.get("type") == 0:
                self._channels.append(TextChannel(loop = self.loop, data = ch))

        return self._channels