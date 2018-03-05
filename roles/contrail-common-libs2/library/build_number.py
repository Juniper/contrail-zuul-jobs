from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

result = dict(
    changed=False,
    original_message='',
    message='',
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            zuul_buildset_id=dict(type='str', required=True),
            version=dict(type='str', required=True),
            build_cache_db_connection_info=dict(type='dict', required=True)
        )
    )
    zuul_buildset_id = module.params['zuul_buildset_id']
    version = module.params['version']
    build_cache_db_connection_info = module.params['build_cache_db_connection_info']
    build_cache_db_connection_info['port'] = int(build_cache_db_connection_info['port'])

    import MySQLdb
    # db exceptions should fail the build, as we are not able to generate a proper build number
    db = MySQLdb.connect(**build_cache_db_connection_info)
    cur = db.cursor()
    cur.execute("SELECT * FROM build_metadata_cache where zuul_buildset_id = %s and version = %s", (zuul_buildset_id, version))
    results = list(cur)
    if len(results) == 0:
        cur.execute("SELECT max(build_number) FROM build_metadata_cache GROUP BY version HAVING version = %s", (version,))
        results = list(cur)
        if len(results) == 0:
            # First build for this version
            build_number = 1
        else:
            build_number = results[0][0] + 1
        cur.execute("INSERT INTO build_metadata_cache (build_number, zuul_buildset_id, version) VALUES (%s, %s, %s)", (build_number, zuul_buildset_id, version))
        db.commit()
    else:
        build_number = results[0][0]
    db.close()
    module.exit_json(ansible_facts={'build_number': build_number}, **result)


if __name__ == "__main__":
    main()
