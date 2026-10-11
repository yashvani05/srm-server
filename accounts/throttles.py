from rest_framework.throttling import SimpleRateThrottle


class LoginThrottle(SimpleRateThrottle):

    scope = "login"

    def parse_rate(self, rate):
        count, _ = rate.split("/")
        return int(count), 15 * 60

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
