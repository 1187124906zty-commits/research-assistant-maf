"""Consequential progress handoffs survive transport failure and parallel work."""
import asyncio
import copy
import json
from pathlib import Path
import tempfile
import unittest

from research_assistant.engine import Session, progress_journal

SCHEMA = {'type': 'object', 'properties': {'answer': {'type': 'string'}},
          'required': ['answer'], 'additionalProperties': False}


class ReportingProvider:
    def __init__(self, fail=False, callback=None):
        self.progress_callback = callback
        self.progress_records = {}
        self.thread_ids = {}
        self.fail = fail
        self.observed = []

    async def ask(self, request):
        key = request['request_id']
        self.thread_ids[key] = 'thread-' + key
        event = {'request_id': key, 'thread_id': self.thread_ids[key],
                 'kind': 'diagnostic_question', 'question': 'Why is the return pending?'}
        self.progress_records[key] = [copy.deepcopy(event)]
        self.observed.append(await self.progress_callback(event))
        # Inspect on disk while this call is still active, not only after return.
        saved = json.loads((Path(request['cwd']) / '.research-assistant/execution.json').read_text(encoding='utf-8'))
        assert saved['calls'][key]['status'] == 'started'
        assert saved['calls'][key]['progress'][0]['question'] == event['question']
        await asyncio.sleep(0)
        if self.fail:
            raise RuntimeError('transport failed after public inquiry')
        return {'answer': key}


class ProgressJournalTests(unittest.IsolatedAsyncioTestCase):
    async def test_live_journal_preserves_callback_and_parallel_request_identity(self):
        seen = []
        async def callback(event):
            seen.append(event['request_id'])
            return {'action': 'continue', 'reason': 'Substantive work is pending.'}
        provider = ReportingProvider(callback=callback)
        with tempfile.TemporaryDirectory() as temporary:
            session = Session(temporary, provider, brief='Bounded evidence inquiry')
            with progress_journal(session):
                answers = await asyncio.gather(*(session.ask('coordinator', {'question': key}, SCHEMA, key) for key in ['one', 'two']))
            self.assertIs(provider.progress_callback, callback)
            self.assertEqual({x['answer'] for x in answers}, {'one', 'two'})
            self.assertEqual(set(seen), {'one', 'two'})
            for key in seen:
                self.assertEqual(session.data['calls'][key]['progress'][0]['thread_id'], 'thread-' + key)
            self.assertTrue(all(x['action'] == 'continue' for x in provider.observed))

    async def test_failure_keeps_progress_and_restores_observer(self):
        provider = ReportingProvider(fail=True)
        with tempfile.TemporaryDirectory() as temporary:
            session = Session(temporary, provider, brief='Bounded evidence inquiry')
            with self.assertRaisesRegex(RuntimeError, 'transport failed'):
                with progress_journal(session):
                    await session.ask('coordinator', {'question': 'one'}, SCHEMA, 'one')
            self.assertIsNone(provider.progress_callback)
            self.assertEqual(session.data['calls']['one']['status'], 'failed')
            self.assertEqual(session.data['calls']['one']['progress'][0]['kind'], 'diagnostic_question')
