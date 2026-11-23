"""Состояния FSM для бота.

Определяет состояния для поиска по треку, по исполнителю,
пагинации результатов и просмотра истории.
"""

from telebot.handler_backends import State, StatesGroup


class SearchStates(StatesGroup):
    top_track = State()
    search_track = State()
    track_pagination = State()
    history_state = State()
