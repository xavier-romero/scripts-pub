def run(plan, args):
    plan.add_service(
        name="nginx",
        config=ServiceConfig(
            image="nginx:1.28",
            ports={
                "test": PortSpec(12345, wait=None)
            },
        ),
    )
