import unittest

from onecode_skill_sanitizer import cli
from onecode_skill_sanitizer import commands
from onecode_skill_sanitizer import router_eval_v3
from onecode_skill_sanitizer import router_evaluation
from onecode_skill_sanitizer import rendering
from onecode_skill_sanitizer import task_pack_v3
from onecode_skill_sanitizer import task_packs


class CliBoundaryTest(unittest.TestCase):
    def test_cli_reexports_task_pack_builders(self):
        self.assertIs(cli.build_task_pack, task_packs.build_task_pack)
        self.assertIs(cli.build_task_pack_v2, task_packs.build_task_pack_v2)
        self.assertIs(cli.build_agent_instructions, task_packs.build_agent_instructions)

    def test_cli_reexports_router_evaluation(self):
        self.assertIs(cli.run_router_eval, router_evaluation.run_router_eval)
        self.assertIs(cli.load_router_eval, router_evaluation.load_router_eval)

    def test_cli_reexports_v3_router_boundaries(self):
        self.assertIs(cli.build_task_pack_v3, task_pack_v3.build_task_pack_v3)
        self.assertIs(cli._run_v3_task_pack_command, commands._run_v3_task_pack_command)
        self.assertIs(cli.render_task_pack_v3_markdown, rendering.render_task_pack_v3_markdown)
        self.assertIs(cli.evaluate_router_v3, router_eval_v3.evaluate_router_v3)
        self.assertIs(cli.load_eval_dataset_v3, router_eval_v3.load_eval_dataset_v3)

    def test_parser_dispatches_to_commands_module(self):
        args = cli.build_parser().parse_args(["list", "--registry", "catalog"])
        self.assertIs(args.func, commands.list_command)


if __name__ == "__main__":
    unittest.main()
