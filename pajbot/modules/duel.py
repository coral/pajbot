import datetime
import logging

from numpy import random

from pajbot.models.command import Command
from pajbot.models.command import CommandExample
from pajbot.models.handler import HandlerManager
from pajbot.modules import BaseModule
from pajbot.modules import ModuleSetting

log = logging.getLogger(__name__)


def init_dueling_variables(user):
    if hasattr(user, 'duel_request'):
        return False
    user.duel_request = False
    user.duel_target = False
    user.duel_price = 0


class DuelModule(BaseModule):

    ID = __name__.split('.')[-1]
    NAME = 'Duel (mini game)'
    DESCRIPTION = 'Let players duel to win or lose points.'
    CATEGORY = 'Game'
    SETTINGS = [
            ModuleSetting(
                key='max_pot',
                label='How many points you can duel for at most',
                type='number',
                required=True,
                placeholder='',
                default=420,
                constraints={
                    'min_value': 0,
                    'max_value': 69000,
                    }),
            ModuleSetting(
                key='message_won',
                label='Winner message | Available arguments: {winner}, {loser}',
                type='text',
                required=True,
                placeholder='{winner} won the duel vs {loser} PogChamp',
                default='{winner} won the duel vs {loser} PogChamp',
                constraints={
                    'min_str_len': 10,
                    'max_str_len': 400,
                    }),
            ModuleSetting(
                key='message_won_points',
                label='Points message | Available arguments: {winner}, {loser}, {total_pot}, {extra_points}',
                type='text',
                required=True,
                placeholder='{winner} won the duel vs {loser} PogChamp . The pot was {total_pot}, the winner gets their bet back + {extra_points} points',
                default='{winner} won the duel vs {loser} PogChamp . The pot was {total_pot}, the winner gets their bet back + {extra_points} points',
                constraints={
                    'min_str_len': 10,
                    'max_str_len': 400,
                    }),
            ModuleSetting(
                key='online_global_cd',
                label='Global cooldown (seconds)',
                type='number',
                required=True,
                placeholder='',
                default=0,
                constraints={
                    'min_value': 0,
                    'max_value': 120,
                    }),
            ModuleSetting(
                key='online_user_cd',
                label='Per-user cooldown (seconds)',
                type='number',
                required=True,
                placeholder='',
                default=5,
                constraints={
                    'min_value': 0,
                    'max_value': 240,
                    }),
                ]

    def load_commands(self, **options):
        self.commands['duel'] = Command.raw_command(self.initiate_duel,
                delay_all=self.settings['online_global_cd'],
                delay_user=self.settings['online_user_cd'],
                description='Initiate a duel with a user',
                examples=[
                    CommandExample(None, '0-point duel',
                        chat='user:!duel Karl_Kons\n'
                        'bot>user:You have challenged Karl_Kons for 0 points',
                        description='Duel Karl_Kons for 0 points').parse(),
                    CommandExample(None, '69-point duel',
                        chat='user:!duel Karl_Kons 69\n'
                        'bot>user:You have challenged Karl_Kons for 69 points',
                        description='Duel Karl_Kons for 69 points').parse(),
                    ],
                )
        self.commands['cancelduel'] = Command.raw_command(
                self.cancel_duel,
                delay_all=0,
                delay_user=10,
                description='Cancel your duel request'
                )
        self.commands['accept'] = Command.raw_command(
                self.accept_duel,
                delay_all=0,
                delay_user=0,
                description='Accept a duel request'
                )
        self.commands['decline'] = Command.raw_command(
                self.decline_duel,
                delay_all=0,
                delay_user=0,
                description='Decline a duel request'
                )
        self.commands['deny'] = self.commands['decline']
        self.commands['duelstatus'] = Command.raw_command(self.status_duel,
                delay_all=0,
                delay_user=5,
                description='Current duel request info')
        self.commands['duelstats'] = Command.raw_command(self.get_duel_stats,
                delay_all=0,
                delay_user=120,
                description='Get your duel statistics')

    def initiate_duel(self, **options):
        """
        Initiate a duel with a user.
        You can also bet points on the winner.
        By default, the maximum amount of points you can spend is 420.

        How to add: !add funccommand duel initiate_duel --cd 0 --usercd 5
        How to use: !duel USERNAME POINTS_TO_BET
        """

        bot = options['bot']
        source = options['source']
        message = options['message']

        if message is None:
            return False

        max_pot = self.settings['max_pot']

        init_dueling_variables(source)

        msg_split = message.split()
        username = msg_split[0]
        user = bot.users.find(username)
        duel_price = 0
        if user is None:
            # No user was found with this username
            return False

        if len(msg_split) > 1:
            try:
                duel_price = int(msg_split[1])
                if duel_price < 0:
                    return False

                if duel_price > max_pot:
                    duel_price = max_pot
            except ValueError:
                pass

        if source.duel_target is not False:
            bot.whisper(source.username, 'You already have a duel request active with {}. Type !cancelduel to cancel your duel request.'.format(source.duel_target.username_raw))
            return False

        if user == source:
            # You cannot duel yourself
            return False

        if user.last_active is None or (datetime.datetime.now() - user._last_active).total_seconds() > 5 * 60:
            bot.whisper(source.username, 'This user has not been active in chat within the last 5 minutes. Get them to type in chat before sending another challenge')
            return False

        if not user.can_afford(duel_price) or not source.can_afford(duel_price):
            bot.whisper(source.username, 'You or your target do not have more than {} points, therefore you cannot duel for that amount.'.format(duel_price))
            return False

        init_dueling_variables(user)

        if user.duel_request is False:
            user.duel_request = source
            source.duel_target = user
            user.duel_price = duel_price
            bot.whisper(user.username, 'You have been challenged to a duel by {} for {} points. You can either !accept or !deny this challenge.'.format(source.username_raw, duel_price))
            bot.whisper(source.username, 'You have challenged {} for {} points'.format(user.username_raw, duel_price))
        else:
            bot.whisper(source.username, 'This person is already being challenged by {}. Ask them to answer the offer by typing !deny or !accept'.format(user.duel_request.username_raw))

    def cancel_duel(self, **options):
        """
        Cancel any duel requests you've sent.

        How to add: !add funccomand cancelduel|duelcancel cancel_duel --cd 0 --usercd 10
        How to use: !cancelduel
        """

        bot = options['bot']
        source = options['source']

        init_dueling_variables(source)

        if source.duel_target is not False:
            bot.whisper(source.username, 'You have cancelled the duel vs {}'.format(source.duel_target.username_raw))
            source.duel_target.duel_request = False
            source.duel_target = False
            source.duel_request = False

    def accept_duel(self, **options):
        """
        Accepts any active duel requests you've received.

        How to add: !add funccommand accept accept_duel --cd 0 --usercd 0
        How to use: !accept
        """

        bot = options['bot']
        source = options['source']

        init_dueling_variables(source)
        duel_tax = 0.3  # 30% tax

        if source.duel_request is not False:
            if not source.can_afford(source.duel_price) or not source.duel_request.can_afford(source.duel_price):
                bot.whisper(source.username, 'Your duel request with {} was cancelled due to one of you not having enough points.'.format(source.duel_request.username_raw))
                bot.whisper(source.duel_request.username, 'Your duel request with {} was cancelled due to one of you not having enough points.'.format(source.username_raw))
                source.duel_request.duel_target = False
                source.duel_request = False
                return False
            source.points -= source.duel_price
            source.duel_request.points -= source.duel_price
            winning_pot = int(source.duel_price * (1.0 - duel_tax))
            participants = [source, source.duel_request]
            winner = random.choice(participants)
            participants.remove(winner)
            loser = participants.pop()
            winner.points += source.duel_price
            winner.points += winning_pot

            bot.duel_manager.user_won(winner, winning_pot)
            bot.duel_manager.user_lost(loser, source.duel_price)

            arguments = {
                    'winner': winner.username,
                    'loser': loser.username,
                    'total_pot': source.duel_price,
                    'extra_points': winning_pot,
                    }

            if source.duel_price > 0:
                message = self.get_phrase('message_won_points', **arguments)
                bot.websocket_manager.emit('notification', {'message': '{} won the duel vs {}'.format(winner.username_raw, loser.username_raw)})
            else:
                message = self.get_phrase('message_won', **arguments)
            bot.say(message)
            source.duel_request.duel_target = False
            source.duel_request = False
            source.duel_price = 0
            HandlerManager.trigger('on_duel_complete',
                    winner, loser,
                    winning_pot, source.duel_price)

    def decline_duel(self, **options):
        """
        Declines any active duel requests you've received.

        How to add: !add funccommand deny|decline decline_duel --cd 0 --usercd 0
        How to use: !decline
        """

        bot = options['bot']
        source = options['source']

        init_dueling_variables(source)

        if source.duel_request is not False:
            bot.whisper(source.username, 'You have declined the duel vs {}'.format(source.duel_request.username_raw))
            bot.whisper(source.duel_request.username, '{} declined the duel challenge with you.'.format(source.username_raw))
            source.duel_request.duel_target = False
            source.duel_request = False

    def status_duel(self, **options):
        """
        Whispers you the current status of your active duel requests/duel targets

        How to add: !add funccommand duelstatus|statusduel status_duel --cd 0 --usercd 5
        How to use: !duelstatus
        """

        bot = options['bot']
        source = options['source']

        init_dueling_variables(source)

        msg = []
        if source.duel_request is not False:
            msg.append('You have a duel request for {} points by {}'.format(source.duel_price, source.duel_request.username_raw))

        if source.duel_target is not False:
            msg.append('You have a duel request against for {} points by {}'.format(source.duel_target.duel_price, source.duel_target.username_raw))

        if len(msg) > 0:
            bot.whisper(source.username, '. '.join(msg))
        else:
            bot.whisper(source.username, 'You have no duel request or duel target. Type !duel USERNAME POT to duel someone!')

    def get_duel_stats(self, **options):
        """
        Whispers the users duel winratio to the user
        """

        bot = options['bot']
        source = options['source']

        if source.duel_stats is None:
            bot.whisper(source.username, 'You have no recorded duels.')
            return True

        bot.whisper(source.username, 'duels: {ds.duels_total} winrate: {ds.winrate:.2f}% streak: {ds.current_streak} profit: {ds.profit}'.format(ds=source.duel_stats))
