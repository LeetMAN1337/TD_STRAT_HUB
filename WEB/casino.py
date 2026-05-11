import random

class DiceGame:
    name = "Кости"
    description = "Угадайте сумму двух кубиков (2–12). Выигрыш x2."

    def play(self, bet):
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        total = die1 + die2
        win = (bet['number'] == total)
        multiplier = 2 if win else 0
        return {
            'die1': die1,
            'die2': die2,
            'total': total,
            'win': win,
            'payout': bet['amount'] * multiplier,
            'message': f"🎉 Поздравляем! Вы угадали сумму {total}!" if win else f"😞 Не угадали. Выпало {total}, ваша ставка {bet['number']}."
        }

class RouletteGame:
    name = "Рулетка"
    description = "Ставка на число от 0 до 36. Выигрыш 36:1."

    def play(self, bet):
        number = random.randint(0, 36)
        win = (bet['number'] == number)
        multiplier = 36 if win else 0
        return {
            'number': number,
            'win': win,
            'payout': bet['amount'] * multiplier,
            'message': f"🎉 Шарик упал на {number}! Вы выиграли x{multiplier}!" if win else f"😞 Шарик упал на {number}. Вы проиграли ставку."
        }

class SlotGame:
    name = "Слоты"
    description = "Три барабана. Если все числа совпадают — выигрыш x10."

    def play(self, bet):
        slots = [random.randint(1, 5) for _ in range(3)]
        win = len(set(slots)) == 1
        multiplier = 10 if win else 0
        return {
            'slots': slots,
            'win': win,
            'payout': bet['amount'] * multiplier,
            'message': f"🎰 {slots[0]} | {slots[1]} | {slots[2]} — {'Джекпот! x10' if win else 'Попробуйте ещё раз'}."
        }

class GuessNumberGame:
    name = "Угадай число"
    description = "Угадайте число от 1 до 10. Выигрыш x3."

    def play(self, bet):
        secret = random.randint(1, 10)
        win = (bet['number'] == secret)
        multiplier = 3 if win else 0
        return {
            'secret': secret,
            'win': win,
            'payout': bet['amount'] * multiplier,
            'message': f"🎉 Загаданное число {secret}! Вы выиграли x{multiplier}!" if win else f"😞 Загаданное число {secret}. Вы проиграли."
        }

class MinesGame:
    name = "Mines"
    description = "Открывайте ячейки, избегая мин."

    def __init__(self, grid_size=5):
        self.grid_size = grid_size
        self.mines = set()
        self.opened = set()

    def init_game(self, mine_count, bet_amount):
        self.mines = set()
        self.opened = set()
        total_cells = self.grid_size ** 2
        if mine_count >= total_cells:
            mine_count = total_cells - 1
        while len(self.mines) < mine_count:
            self.mines.add(random.randint(0, total_cells - 1))
        self.bet_amount = bet_amount
        self.finished = False
        self.multiplier = 1.0
        self.current_payout = bet_amount

    def reveal_cell(self, cell_index):
        if self.finished:
            return {'error': 'Игра завершена.'}
        if cell_index in self.opened:
            return {'error': 'Ячейка уже открыта.'}
        self.opened.add(cell_index)
        if cell_index in self.mines:
            self.finished = True
            return {
                'mine': True,
                'win': False,
                'payout': 0,
                'multiplier': 0,
                'message': '💥 Вы попали на мину! Ставка потеряна.'
            }
        safe_opened = len(self.opened)
        safe_cells = self.grid_size ** 2 - len(self.mines)
        self.multiplier = round((safe_cells / (safe_cells - safe_opened)) ** safe_opened, 2)
        self.current_payout = int(self.bet_amount * self.multiplier)
        if len(self.opened) == safe_cells:
            self.finished = True
            return {
                'mine': False,
                'win': True,
                'payout': self.current_payout,
                'multiplier': self.multiplier,
                'message': f'🏆 Вы открыли все безопасные ячейки! Выигрыш x{self.multiplier}'
            }
        return {
            'mine': False,
            'win': None,
            'payout': self.current_payout,
            'multiplier': self.multiplier,
            'message': f'Открыта ячейка {cell_index}. Множитель x{self.multiplier}'
        }

    def cash_out(self):
        if self.finished:
            return {'error': 'Игра уже завершена.'}
        self.finished = True
        return {
            'win': True,
            'payout': self.current_payout,
            'multiplier': self.multiplier,
            'message': f'💰 Вы забрали выигрыш x{self.multiplier}!'
        }