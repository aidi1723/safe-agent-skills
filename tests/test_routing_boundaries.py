import unittest

from onecode_skill_sanitizer import router
from onecode_skill_sanitizer import routing_execution
from onecode_skill_sanitizer import routing_profiles


class RoutingBoundaryTest(unittest.TestCase):
    def test_router_reexports_profile_api(self):
        self.assertIs(router.build_task_profile, routing_profiles.build_task_profile)
        self.assertIs(router.score_bundle_for_profile, routing_profiles.score_bundle_for_profile)

    def test_router_reexports_execution_api(self):
        self.assertIs(router.build_execution_graph, routing_execution.build_execution_graph)
        self.assertIs(router.build_contract_graph, routing_execution.build_contract_graph)
        self.assertIs(router.build_contract_diagnostics, routing_execution.build_contract_diagnostics)


if __name__ == "__main__":
    unittest.main()
