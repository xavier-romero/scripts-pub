def run(plan, args):
    plan.add_service(
        name="nginx",
        config=ServiceConfig(
            image="nginx:1.28",
            files={
                "/keep_me": Directory(persistent_key="keepme")
            }
        ),
    )
