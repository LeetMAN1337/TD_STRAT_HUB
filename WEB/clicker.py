import math
from datetime import datetime, date


class ClickerGame:
    def __init__(self):
        self.base_click_price = 10
        self.base_auto_price = 50
        self.base_super_price = 200
        self.click_price_multiplier = 2
        self.auto_price_multiplier = 2
        self.super_price_multiplier = 10
        self.daily_convert_limit = 5

    def get_state(self, user):
        return {
            'points': user.points,
            'clicker_points': user.clicker_points,
            'click_power': user.click_power,
            'auto_click_power': user.auto_click_power,
            'click_price': self.get_click_price(user),
            'auto_price': self.get_auto_price(user),
            'super_price': self.get_super_price(user),
            'converts_left': self.get_converts_left(user)
        }

    def get_click_price(self, user):
        return int(self.base_click_price * (self.click_price_multiplier ** (user.click_power - 1)))

    def get_auto_price(self, user):
        return int(self.base_auto_price * (self.auto_price_multiplier ** max(user.auto_click_power, 0)))

    def get_super_price(self, user):
        total_upgrades = (user.click_power - 1) + user.auto_click_power
        super_level = max(total_upgrades // 10, 0)
        return int(self.base_super_price * (self.super_price_multiplier ** super_level))

    def get_converts_left(self, user):
        today = date.today()
        if user.last_convert_date != today:
            user.daily_converts_used = 0
            user.last_convert_date = today
        return self.daily_convert_limit - user.daily_converts_used

    def click(self, user):
        user.clicker_points += user.click_power
        return self.get_state(user)

    def buy_upgrade(self, user, upgrade_type):
        if upgrade_type == 'click':
            price = self.get_click_price(user)
            if user.clicker_points < price:
                return {'error': 'Недостаточно очков кликера!'}
            user.clicker_points -= price
            user.click_power += 1
        elif upgrade_type == 'auto':
            price = self.get_auto_price(user)
            if user.clicker_points < price:
                return {'error': 'Недостаточно очков кликера!'}
            user.clicker_points -= price
            user.auto_click_power += 1
        elif upgrade_type == 'super':
            price = self.get_super_price(user)
            if user.clicker_points < price:
                return {'error': 'Недостаточно очков кликера!'}
            user.clicker_points -= price
            user.click_power += 5
            user.auto_click_power += 5
        return self.get_state(user)

    def convert(self, user):
        converts_left = self.get_converts_left(user)
        if converts_left <= 0:
            return {'error': 'Вы исчерпали лимит конвертаций на сегодня (5 раз в день)!'}
        if user.clicker_points <= 0:
            return {'error': 'Нечего конвертировать!'}
        converted = int(math.log(user.clicker_points, 3))
        if converted <= 0:
            return {'error': 'Слишком мало очков для конвертации!'}
        user.points += converted
        user.clicker_points = 0
        user.daily_converts_used += 1
        user.last_convert_date = date.today()
        return self.get_state(user)