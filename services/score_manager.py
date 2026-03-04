from datetime import datetime
from new_model.result_new import ResultNew
from new_model.head_model.fight_new import FightNew
from database.db import db
from config import SCORE_VALUES, OSAEKOMI_TIMES, MAX_PENALTIES
from sqlalchemy.orm.attributes import flag_modified
from new_model.Enums import FightStatus

class ScoreManager:
    def __init__(self, fight_id):
        self.fight = FightNew.query.get(fight_id)
        if not self.fight:
            raise ValueError(f"Fight {fight_id} not found")

        # Создаем или получаем результат
        if not self.fight.result:
            self.result = ResultNew(fight_id=fight_id)
            db.session.add(self.result)
            db.session.commit()
        else:
            self.result = self.fight.result

    def rematch_fight(self):
        """Переигровка — полный сброс результата и статуса боя"""
        # Удаляем результат из БД
        if self.fight.result:
            db.session.delete(self.fight.result)
            db.session.flush()  # чтобы delete применился до commit
            self.result = None

        # Сбрасываем статус боя обратно в SCHEDULED
        self.fight.status = FightStatus.SCHEDULED
        self.fight.start_time = None
        self.fight.end_time = None

        db.session.commit()

        return {
            'success': True,
            'message': 'Бой сброшен для переигровки',
            'fight_id': self.fight.id,
            'status': self.fight.status.value
        }

    def _add_event(self, event_data):
        """Добавить событие в единый журнал боя"""
        # Инициализируем журнал событий, если его нет (на всякий случай)
        if self.fight.events_log is None:
            self.fight.events_log = []

        # Генерируем уникальный ID события
        event_data['id'] = len(self.fight.events_log) + 1
        event_data['match_time'] = self._get_current_match_time()
        event_data['timestamp'] = datetime.utcnow().isoformat()

        # Добавляем событие в журнал боя
        self.fight.events_log.append(event_data)

        # ВАЖНО: Помечаем JSON поле как измененное
        flag_modified(self.fight, "events_log")

        return event_data

    def _get_current_match_time(self):
        """Получить текущее время боя (минута:секунда)"""
        if self.fight.start_time:
            elapsed = (datetime.utcnow() - self.fight.start_time).total_seconds()
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            return f"{minutes}:{seconds:02d}"
        return "0:00"

    def add_yuko(self, athlete_color):
        """Добавить оценку ЮКО"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        self.result.add_score(athlete_color, 'YUKO')

        # Добавляем событие в журнал
        event = self._add_event({
            'type': 'SCORE',
            'subtype': 'YUKO',
            'athlete_color': athlete_color,
            'points': SCORE_VALUES['YUKO'],
            'description': f'ЮКО - {athlete_color}',
            'details': {
                'score_value': SCORE_VALUES['YUKO'],
                'total_yuko': self.result.white_yuko if athlete_color == 'WHITE' else self.result.blue_yuko
            }
        })

        db.session.commit()

        return {
            'success': True,
            'message': f'ЮКО добавлено для {athlete_color}',
            'event': event,
            'white_score': self.result.white_score,
            'blue_score': self.result.blue_score,
            'white_yuko': self.result.white_yuko,
            'blue_yuko': self.result.blue_yuko
        }

    def add_wazaari(self, athlete_color, technique=None):
        """Добавить оценку ВАЗА-АРИ"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        self.result.add_score(athlete_color, 'WAZAARI', technique)

        # Добавляем событие в журнал
        event = self._add_event({
            'type': 'SCORE',
            'subtype': 'WAZAARI',
            'athlete_color': athlete_color,
            'points': SCORE_VALUES['WAZAARI'],
            'technique': technique,
            'description': f'ВАЗА-АРИ - {athlete_color}' + (f' ({technique})' if technique else ''),
            'details': {
                'score_value': SCORE_VALUES['WAZAARI'],
                'technique': technique,
                'total_wazaari': self.result.white_wazaari if athlete_color == 'WHITE' else self.result.blue_wazaari
            }
        })

        db.session.commit()

        # Проверяем, не привело ли это к победе (2 ваза-ари = иппон)
        if self.result.victory_type == 'WAZAARI_AWASETE_IPPON':
            self._complete_fight_for_winner()
            event['resulted_in_victory'] = True
            event['details']['victory_type'] = 'WAZAARI_AWASETE_IPPON'
            flag_modified(self.fight, "events_log")

        return {
            'success': True,
            'message': f'ВАЗА-АРИ добавлено для {athlete_color}',
            'event': event,
            'white_score': self.result.white_score,
            'blue_score': self.result.blue_score,
            'white_wazaari': self.result.white_wazaari,
            'blue_wazaari': self.result.blue_wazaari,
            'victory': self.result.victory_type if self.result.victory_type else None
        }

    def add_ippon(self, athlete_color, technique=None):
        """Добавить оценку ИППОН"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        self.result.add_score(athlete_color, 'IPPON', technique)

        db.session.commit()

        # Автоматически завершаем бой при ИППОН
        self._complete_fight_for_winner()

        return {
            'success': True,
            'message': f'ИППОН добавлено для {athlete_color}. Схватка завершена!',
            'winner': self.result.winner_id,
            'victory_type': self.result.victory_type
        }


    def start_osaekomi(self, athlete_color):
        """Начать отсчет времени удержания"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        # Если уже есть активное осаекоми, сначала останавливаем его
        if self.result.osaekomi_start_time:
            self.result.stop_osaekomi()

        self.result.start_osaekomi(athlete_color)

        # Добавляем событие в журнал
        event = self._add_event({
            'type': 'OSAEKOMI',
            'subtype': 'START',
            'athlete_color': athlete_color,
            'description': f'Начало ОСАЕКОМИ - {athlete_color}',
            'details': {
                'start_time': datetime.utcnow().isoformat()
            }
        })

        db.session.commit()

        return {
            'success': True,
            'message': f'ОСАЕКОМИ начато для {athlete_color}',
            'event': event,
            'start_time': self.result.osaekomi_start_time.isoformat()
        }

    def stop_osaekomi(self):
        """Остановить отсчет времени удержания"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        if not self.result.osaekomi_start_time:
            return {'success': False, 'message': 'Нет активного ОСАЕКОМИ'}

        duration, action = self.result.stop_osaekomi()

        result = {
            'success': True,
            'message': f'ОСАЕКОМИ остановлено после {duration} секунд',
            'duration': duration,
            'osaekomi_duration': self.result.osaekomi_duration
        }

        if duration >= OSAEKOMI_TIMES['IPPON']:
            result['ippon_awarded'] = True
            result['winner'] = self.result.winner_id
            self._complete_fight_for_winner()
        elif duration >= OSAEKOMI_TIMES['WAZAARI']:
            result['wazaari_awarded'] = True
            if self.result.victory_type == 'WAZAARI_AWASETE_IPPON':
                self._complete_fight_for_winner()

        db.session.commit()

        return result
    def add_penalty(self, athlete_color, penalty_type):
        """Добавить штраф"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        self.result.add_penalty(athlete_color, penalty_type)

        # Получаем количество штрафов после добавления
        penalty_count = self.result.get_penalty_count(athlete_color)

        # Добавляем событие в журнал
        event = self._add_event({
            'type': 'PENALTY',
            'subtype': penalty_type,
            'athlete_color': athlete_color,
            'description': f'{penalty_type} - {athlete_color}',
            'details': {
                'penalty_count': penalty_count,
                'max_penalties': MAX_PENALTIES.get('SHIDO', 3)
            }
        })

        db.session.commit()

        # Проверяем, не привело ли это к победе
        if penalty_type.upper() == 'HANSOKU_MAKE':
            event['resulted_in_victory'] = True
            opponent_color = 'BLUE' if athlete_color.upper() == 'WHITE' else 'WHITE'
            opponent_id = self.fight.white_athlete_id if opponent_color == 'WHITE' else self.fight.blue_athlete_id
            event['description'] += f' → ПОБЕДА {opponent_color}'

            self.result.victory_type = 'HANSOKU_MAKE'
            self.result.winner_id = opponent_id
            flag_modified(self.fight, "events_log")
            db.session.commit()

            self._complete_fight_for_winner()

            return {
                'success': True,
                'message': f'{penalty_type} добавлен для {athlete_color}. Дисквалификация!',
                'event': event,
                'winner': opponent_id,
                'victory_type': 'HANSOKU_MAKE'
            }

        # Проверяем, не достиг ли спортсмен 3 шидо
        if penalty_type.upper() == 'SHIDO' and penalty_count >= MAX_PENALTIES.get('SHIDO', 3):
            event['resulted_in_victory'] = True
            event['details']['victory_reason'] = 'MAX_PENALTIES'
            self._complete_fight_for_winner()

        return {
            'success': True,
            'message': f'{penalty_type} добавлен для {athlete_color}',
            'event': event,
            'white_penalties': self.result.white_penalties,
            'blue_penalties': self.result.blue_penalties,
            'white_penalty_count': self.result.get_penalty_count('WHITE'),
            'blue_penalty_count': self.result.get_penalty_count('BLUE')
        }

    def undo_last_action(self):
        """Отменить последнее действие"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        success, action = self.result.undo_last_action()
        if success:
            # Также удаляем последнее событие из журнала боя
            if self.fight.events_log:
                removed_event = self.fight.events_log.pop()
                flag_modified(self.fight, "events_log")

            db.session.commit()
            return {
                'success': True,
                'message': 'Последнее действие отменено',
                'action_type': action['type'] if action else None,
                'removed_event': removed_event if 'removed_event' in locals() else None
            }
        else:
            return {'success': False, 'message': 'Нет действий для отмены'}

    def reset_scores(self):
        """Сбросить все оценки и штрафы"""
        if self.fight.status != 'LIVE':
            return {'success': False, 'message': 'Схватка не активна'}

        self.result.reset_scores()

        # Очищаем журнал событий
        self.fight.events_log = []
        flag_modified(self.fight, "events_log")

        # Добавляем событие сброса
        self._add_event({
            'type': 'SYSTEM',
            'subtype': 'RESET',
            'description': 'Сброс всех оценок и штрафов',
            'details': {
                'reset_time': datetime.utcnow().isoformat()
            }
        })

        db.session.commit()

        return {
            'success': True,
            'message': 'Все оценки и штрафы сброшены',
            'event': {
                'type': 'RESET',
                'timestamp': datetime.utcnow().isoformat()
            },
            'white_score': self.result.white_score,
            'blue_score': self.result.blue_score
        }

    def add_action_to_log(self, action_type, description, athlete_color=None, details=None):
        """Добавить произвольное действие в журнал"""
        if self.fight.status not in ['LIVE', 'IN_PROGRESS']:
            return {'success': False, 'message': 'Схватка не активна'}

        event = {
            'type': 'CUSTOM',
            'subtype': action_type.upper(),
            'description': description,
            'athlete_color': athlete_color.upper() if athlete_color else None,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }

        added_event = self._add_event(event)
        db.session.commit()

        return {
            'success': True,
            'message': 'Действие добавлено в журнал',
            'event': added_event
        }

    def save_fight_events(self, events_data):
        """Сохранить все события боя одним запросом"""
        try:
            if self.fight.status not in ['LIVE', 'IN_PROGRESS', 'COMPLETED']:
                return {'success': False, 'message': 'Невозможно сохранить события'}

            # Инициализируем журнал, если его нет
            if self.fight.events_log is None:
                self.fight.events_log = []

            added_events = []

            # events_data должен быть списком событий
            for event in events_data:
                event_data = {
                    'type': event.get('type', 'UNKNOWN'),
                    'subtype': event.get('subtype'),
                    'athlete_color': event.get('athlete_color'),
                    'timestamp': event.get('timestamp', datetime.utcnow().isoformat()),
                    'match_time': event.get('match_time', self._get_current_match_time()),
                    'details': event.get('details', {}),
                    'description': event.get('description', '')
                }

                # Добавляем ID
                event_data['id'] = len(self.fight.events_log) + 1

                # Добавляем в журнал боя
                self.fight.events_log.append(event_data)
                added_events.append(event_data)

            flag_modified(self.fight, "events_log")
            db.session.commit()

            return {
                'success': True,
                'message': f'Сохранено {len(added_events)} событий',
                'total_events': len(self.fight.events_log),
                'added_events': added_events
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Ошибка сохранения: {str(e)}'}

    def get_action_log(self, limit=50, offset=0):
        """Получить журнал действий (для совместимости)"""
        actions = []

        if self.fight.events_log:
            # Используем новый формат журнала
            for event in self.fight.events_log:
                action_data = {
                    'id': event.get('id', 0),
                    'action_type': event.get('type', 'UNKNOWN'),
                    'description': event.get('description', ''),
                    'athlete_color': event.get('athlete_color'),
                    'timestamp': event.get('timestamp'),
                    'match_time': event.get('match_time'),
                    'details': event.get('details', {})
                }
                actions.append(action_data)

        # Применяем пагинацию
        total = len(actions)
        if offset > 0:
            actions = actions[offset:]
        if limit > 0:
            actions = actions[:limit]

        return {
            'success': True,
            'actions': actions,
            'total_count': total
        }

    def get_fight_timeline(self):
        """Получить всю хронологию боя"""
        if not self.fight.events_log:
            return {
                'success': True,
                'fight_id': self.fight.id,
                'events': [],
                'summary': {
                    'total_events': 0,
                    'white_actions': 0,
                    'blue_actions': 0,
                    'scores': 0,
                    'penalties': 0,
                    'osaekomi_events': 0,
                    'custom_events': 0
                }
            }

        # Анализируем события
        white_actions = [e for e in self.fight.events_log if e.get('athlete_color') == 'WHITE']
        blue_actions = [e for e in self.fight.events_log if e.get('athlete_color') == 'BLUE']
        scores = [e for e in self.fight.events_log if e.get('type') == 'SCORE']
        penalties = [e for e in self.fight.events_log if e.get('type') == 'PENALTY']
        osaekomi_events = [e for e in self.fight.events_log if e.get('type') == 'OSAEKOMI']
        custom_events = [e for e in self.fight.events_log if e.get('type') in ['CUSTOM', 'SYSTEM']]

        return {
            'success': True,
            'fight_id': self.fight.id,
            'fight_status': self.fight.status,
            'events': self.fight.events_log,
            'summary': {
                'total_events': len(self.fight.events_log),
                'white_actions': len(white_actions),
                'blue_actions': len(blue_actions),
                'scores': len(scores),
                'penalties': len(penalties),
                'osaekomi_events': len(osaekomi_events),
                'custom_events': len(custom_events),
                'white_score': self.result.white_score,
                'blue_score': self.result.blue_score,
                'white_penalty_count': self.result.get_penalty_count('WHITE'),
                'blue_penalty_count': self.result.get_penalty_count('BLUE')
            }
        }

    def get_match_summary(self):
        """Получить сводку матча с группировкой по типам событий"""
        if not self.fight.events_log:
            return {'success': False, 'message': 'Нет данных о событиях'}

        summary = {
            'white': {
                'scores': [],
                'penalties': [],
                'osaekomi': [],
                'total_points': self.result.white_score,
                'yuko_count': self.result.white_yuko,
                'wazaari_count': self.result.white_wazaari,
                'ippon_count': self.result.white_ippon,
                'penalty_count': self.result.get_penalty_count('WHITE')
            },
            'blue': {
                'scores': [],
                'penalties': [],
                'osaekomi': [],
                'total_points': self.result.blue_score,
                'yuko_count': self.result.blue_yuko,
                'wazaari_count': self.result.blue_wazaari,
                'ippon_count': self.result.blue_ippon,
                'penalty_count': self.result.get_penalty_count('BLUE')
            },
            'match_events': [],
            'timeline': [],
            'key_moments': []
        }

        for event in self.fight.events_log:
            athlete = event.get('athlete_color')
            event_type = event.get('type')
            event_subtype = event.get('subtype')

            # Формируем запись для таймлайна
            timeline_event = {
                'id': event.get('id'),
                'time': event.get('match_time', ''),
                'description': event.get('description', ''),
                'type': event_type,
                'subtype': event_subtype,
                'athlete_color': athlete,
                'timestamp': event.get('timestamp')
            }

            # Добавляем в ключевые моменты если это важное событие
            if event_type == 'SCORE' or event_subtype in ['HANSOKU_MAKE', 'IPPON', 'WAZAARI_AWASETE_IPPON']:
                key_moment = timeline_event.copy()
                key_moment['details'] = event.get('details', {})
                summary['key_moments'].append(key_moment)

            # Группируем по спортсменам
            if athlete == 'WHITE':
                if event_type == 'SCORE':
                    summary['white']['scores'].append(event)
                elif event_type == 'PENALTY':
                    summary['white']['penalties'].append(event)
                elif event_type == 'OSAEKOMI':
                    summary['white']['osaekomi'].append(event)
            elif athlete == 'BLUE':
                if event_type == 'SCORE':
                    summary['blue']['scores'].append(event)
                elif event_type == 'PENALTY':
                    summary['blue']['penalties'].append(event)
                elif event_type == 'OSAEKOMI':
                    summary['blue']['osaekomi'].append(event)
            else:
                summary['match_events'].append(event)

            summary['timeline'].append(timeline_event)

        # Сортируем таймлайн по времени
        summary['timeline'] = sorted(summary['timeline'], key=lambda x: x.get('time', '0:00'))
        summary['key_moments'] = sorted(summary['key_moments'], key=lambda x: x.get('time', '0:00'))

        return {
            'success': True,
            'fight_id': self.fight.id,
            'fight_status': self.fight.status,
            'summary': summary,
            'victory_type': self.result.victory_type,
            'winner_id': self.result.winner_id,
            'match_duration': self._get_match_duration()
        }

    def _get_match_duration(self):
        """Получить длительность матча"""
        if self.fight.start_time and self.fight.end_time:
            duration = (self.fight.end_time - self.fight.start_time).total_seconds()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}:{seconds:02d}"
        elif self.fight.start_time:
            duration = (datetime.utcnow() - self.fight.start_time).total_seconds()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}:{seconds:02d}"
        return None

    def get_current_scores(self):
        """Получить текущие оценки"""
        return {
            'success': True,
            'white': {
                'score': self.result.white_score,
                'yuko': self.result.white_yuko,
                'wazaari': self.result.white_wazaari,
                'ippon': self.result.white_ippon,
                'penalties': self.result.white_penalties,
                'penalty_count': self.result.get_penalty_count('WHITE')
            },
            'blue': {
                'score': self.result.blue_score,
                'yuko': self.result.blue_yuko,
                'wazaari': self.result.blue_wazaari,
                'ippon': self.result.blue_ippon,
                'penalties': self.result.blue_penalties,
                'penalty_count': self.result.get_penalty_count('BLUE')
            },
            'osaekomi': {
                'active': self.result.osaekomi_start_time is not None,
                'athlete_color': self.result.osaekomi_athlete_color,
                'time': self.result.osaekomi_time if hasattr(self.result, 'osaekomi_time') else 0,
                'total_duration': self.result.osaekomi_duration
            },
            'victory_type': self.result.victory_type,
            'winner_id': self.result.winner_id,
            'fight_status': self.fight.status
        }
    def _complete_fight_for_winner(self):
        """Завершить бой для текущего победителя"""
        if self.result.winner_id:
            self.fight.complete_fight(
                winner_id=self.result.winner_id,
                victory_type=self.result.victory_type,
                details=self.result.details
            )

            # Добавляем событие завершения боя
            self._add_event({
                'type': 'SYSTEM',
                'subtype': 'FIGHT_END',
                'description': f'Бой завершен. Победитель: {self.result.winner_id} ({self.result.victory_type})',
                'details': {
                    'winner_id': self.result.winner_id,
                    'victory_type': self.result.victory_type,
                    'end_time': datetime.utcnow().isoformat()
                }
            })

            flag_modified(self.fight, "events_log")
            db.session.commit()

    def clear_events_log(self):
        """Очистить журнал событий"""
        self.fight.events_log = []
        flag_modified(self.fight, "events_log")
        db.session.commit()
        return {'success': True, 'message': 'Журнал событий очищен'}

    def export_events(self, format='json'):
        """Экспортировать события в указанном формате"""
        if not self.fight.events_log:
            return {'success': False, 'message': 'Нет событий для экспорта'}

        if format.lower() == 'json':
            return {
                'success': True,
                'format': 'json',
                'fight_id': self.fight.id,
                'events': self.fight.events_log,
                'metadata': {
                    'export_time': datetime.utcnow().isoformat(),
                    'total_events': len(self.fight.events_log),
                    'fight_status': self.fight.status
                }
            }
        else:
            return {'success': False, 'message': f'Формат {format} не поддерживается'}