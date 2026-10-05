# MarkLogic 10: 392 endpoint contracts

Read only the relevant section of `v10.md`, using the inclusive line ranges below.
Every row includes all supplied parameters, request/response headers, response description, privileges, usage and examples where present in the vendor export.
A wrapper covers the operation, not necessarily every parameter or view; use raw HTTP when its signature or validator is narrower.

| Endpoint | MLClient route | Lines |
| --- | --- | --- |
| `POST /admin/v1/cluster-config` | Raw HTTP / custom ApiCall | 6-150 |
| `DELETE /admin/v1/host-config` | Raw HTTP / custom ApiCall | 151-257 |
| `POST /admin/v1/init` | Raw HTTP / custom ApiCall | 258-455 |
| `POST /admin/v1/instance-admin` | Raw HTTP / custom ApiCall | 456-546 |
| `GET /admin/v1/server-config` | `ml.admin.get_server_config` (sync and async) | 547-662 |
| `GET /admin/v1/timestamp` | `ml.admin.get_timestamp` (sync and async) | 663-751 |
| `HEAD /admin/v1/timestamp` | Raw HTTP / custom ApiCall | 752-783 |
| `GET /manage/v1/domains` | Raw HTTP / custom ApiCall | 784-835 |
| `GET /manage/v2` | Raw HTTP / custom ApiCall | 836-964 |
| `POST /manage/v2` | Raw HTTP / custom ApiCall | 965-1009 |
| `GET /manage/v2?view=describe` | Raw HTTP / custom ApiCall | 1010-1194 |
| `GET /manage/v2?view=query` | Raw HTTP / custom ApiCall | 1195-1332 |
| `GET /manage/v2?view=status` | Raw HTTP / custom ApiCall | 1333-2144 |
| `GET /manage/v2/amps` | Raw HTTP / custom ApiCall | 2145-2244 |
| `POST /manage/v2/amps` | Raw HTTP / custom ApiCall | 2245-2325 |
| `DELETE /manage/v2/amps/{id&#124;name}` | Raw HTTP / custom ApiCall | 2326-2370 |
| `GET /manage/v2/amps/{id&#124;name}` | Raw HTTP / custom ApiCall | 2371-2507 |
| `GET /manage/v2/amps/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 2508-2572 |
| `PUT /manage/v2/amps/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 2573-2641 |
| `GET /manage/v2/certificate-authorities` | Raw HTTP / custom ApiCall | 2642-2738 |
| `POST /manage/v2/certificate-authorities` | Raw HTTP / custom ApiCall | 2739-2859 |
| `DELETE /manage/v2/certificate-authorities/{id&#124;name}` | Raw HTTP / custom ApiCall | 2860-2901 |
| `GET /manage/v2/certificate-authorities/{id&#124;name}` | Raw HTTP / custom ApiCall | 2902-2954 |
| `GET /manage/v2/certificate-authorities/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 2955-3008 |
| `PUT /manage/v2/certificate-revocation-lists` | Raw HTTP / custom ApiCall | 3009-3051 |
| `GET /manage/v2/certificate-templates` | Raw HTTP / custom ApiCall | 3052-3160 |
| `POST /manage/v2/certificate-templates` | Raw HTTP / custom ApiCall | 3161-3296 |
| `DELETE /manage/v2/certificate-templates/{id&#124;name}` | Raw HTTP / custom ApiCall | 3297-3337 |
| `GET /manage/v2/certificate-templates/{id&#124;name}` | Raw HTTP / custom ApiCall | 3338-3466 |
| `POST /manage/v2/certificate-templates/{id&#124;name}` | Raw HTTP / custom ApiCall | 3467-3586 |
| `GET /manage/v2/certificate-templates/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 3587-3698 |
| `PUT /manage/v2/certificate-templates/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 3699-3810 |
| `GET /manage/v2/certificates` | Raw HTTP / custom ApiCall | 3811-3906 |
| `POST /manage/v2/certificates` | Raw HTTP / custom ApiCall | 3907-3985 |
| `DELETE /manage/v2/certificates/{id&#124;name}` | Raw HTTP / custom ApiCall | 3986-4025 |
| `GET /manage/v2/certificates/{id&#124;name}` | Raw HTTP / custom ApiCall | 4026-4149 |
| `GET /manage/v2/certificates/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 4150-4269 |
| `GET /manage/v2/clusters` | Raw HTTP / custom ApiCall | 4270-4406 |
| `POST /manage/v2/clusters` | Raw HTTP / custom ApiCall | 4407-4552 |
| `GET /manage/v2/clusters?view=metrics` | Raw HTTP / custom ApiCall | 4553-4610 |
| `DELETE /manage/v2/clusters/{id&#124;name}` | Raw HTTP / custom ApiCall | 4611-4654 |
| `GET /manage/v2/clusters/{id&#124;name}` | Raw HTTP / custom ApiCall | 4655-4785 |
| `POST /manage/v2/clusters/{id&#124;name}` | Raw HTTP / custom ApiCall | 4786-5002 |
| `GET /manage/v2/clusters/{id&#124;name}?view=metrics` | Raw HTTP / custom ApiCall | 5003-5056 |
| `GET /manage/v2/clusters/{id&#124;name}?view=status` | Raw HTTP / custom ApiCall | 5057-5239 |
| `GET /manage/v2/clusters/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 5240-5317 |
| `PUT /manage/v2/clusters/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 5318-5403 |
| `DELETE /manage/v2/credentials/properties` | Raw HTTP / custom ApiCall | 5404-5445 |
| `GET /manage/v2/credentials/properties` | Raw HTTP / custom ApiCall | 5446-5511 |
| `PUT /manage/v2/credentials/properties` | Raw HTTP / custom ApiCall | 5512-5584 |
| `GET /manage/v2/credentials/secure` | Raw HTTP / custom ApiCall | 5585-5671 |
| `POST /manage/v2/credentials/secure` | Raw HTTP / custom ApiCall | 5672-5802 |
| `GET /manage/v2/databases` | `ml.manage.databases.get_list` (sync and async) | 5803-5936 |
| `POST /manage/v2/databases` | `ml.manage.databases.create` (sync and async) | 5937-6860 |
| `GET /manage/v2/databases?view=metrics` | `ml.manage.databases.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 6861-6914 |
| `DELETE /manage/v2/databases/{id&#124;name}` | `ml.manage.databases.delete` (sync and async) | 6915-6963 |
| `GET /manage/v2/databases/{id&#124;name}` | `ml.manage.databases.get` (sync and async) | 6964-7099 |
| `POST /manage/v2/databases/{id&#124;name}` | `ml.manage.databases.post` (sync and async) | 7100-7509 |
| `GET /manage/v2/databases/{id&#124;name}?view=counts` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 7510-7611 |
| `GET /manage/v2/databases/{id&#124;name}?view=package` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 7612-7658 |
| `GET /manage/v2/databases/{id&#124;name}?view=status` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 7659-8196 |
| `GET /manage/v2/databases/{id&#124;name}/alert` | Raw HTTP / custom ApiCall | 8197-8315 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions` | Raw HTTP / custom ApiCall | 8316-8407 |
| `POST /manage/v2/databases/{id&#124;name}/alert/actions` | Raw HTTP / custom ApiCall | 8408-8486 |
| `DELETE /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}` | Raw HTTP / custom ApiCall | 8487-8529 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}` | Raw HTTP / custom ApiCall | 8530-8652 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 8653-8717 |
| `PUT /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 8718-8790 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 8791-8881 |
| `POST /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 8882-8967 |
| `DELETE /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}` | Raw HTTP / custom ApiCall | 8968-9010 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}` | Raw HTTP / custom ApiCall | 9011-9131 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 9132-9200 |
| `PUT /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 9201-9277 |
| `DELETE /manage/v2/databases/{id&#124;name}/alert/configs` | Raw HTTP / custom ApiCall | 9278-9322 |
| `GET /manage/v2/databases/{id&#124;name}/alert/configs` | Raw HTTP / custom ApiCall | 9323-9453 |
| `POST /manage/v2/databases/{id&#124;name}/alert/configs` | Raw HTTP / custom ApiCall | 9454-9565 |
| `GET /manage/v2/databases/{id&#124;name}/alert/configs/properties` | Raw HTTP / custom ApiCall | 9566-9642 |
| `PUT /manage/v2/databases/{id&#124;name}/alert/configs/properties` | Raw HTTP / custom ApiCall | 9643-9730 |
| `GET /manage/v2/databases/{id&#124;name}/cpf-configs` | Raw HTTP / custom ApiCall | 9731-9832 |
| `POST /manage/v2/databases/{id&#124;name}/cpf-configs` | Raw HTTP / custom ApiCall | 9833-9945 |
| `DELETE /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}` | Raw HTTP / custom ApiCall | 9946-9982 |
| `GET /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}` | Raw HTTP / custom ApiCall | 9983-10107 |
| `GET /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}/properties` | Raw HTTP / custom ApiCall | 10108-10175 |
| `PUT /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}/properties` | Raw HTTP / custom ApiCall | 10176-10246 |
| `GET /manage/v2/databases/{id&#124;name}/domains` | Raw HTTP / custom ApiCall | 10247-10350 |
| `POST /manage/v2/databases/{id&#124;name}/domains` | Raw HTTP / custom ApiCall | 10351-10444 |
| `DELETE /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}` | Raw HTTP / custom ApiCall | 10445-10481 |
| `GET /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}` | Raw HTTP / custom ApiCall | 10482-10606 |
| `GET /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 10607-10684 |
| `PUT /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 10685-10763 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep` | Raw HTTP / custom ApiCall | 10764-10885 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs` | Raw HTTP / custom ApiCall | 10886-10987 |
| `POST /manage/v2/databases/{id&#124;name}/flexrep/configs` | Raw HTTP / custom ApiCall | 10988-11044 |
| `DELETE /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}` | Raw HTTP / custom ApiCall | 11045-11082 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}` | Raw HTTP / custom ApiCall | 11083-11209 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 11210-11264 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 11265-11318 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets` | Raw HTTP / custom ApiCall | 11319-11421 |
| `POST /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets` | Raw HTTP / custom ApiCall | 11422-11572 |
| `DELETE /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}` | Raw HTTP / custom ApiCall | 11573-11611 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}` | Raw HTTP / custom ApiCall | 11612-11738 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 11739-11857 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 11858-11979 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/properties` | Raw HTTP / custom ApiCall | 11980-12035 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/properties` | Raw HTTP / custom ApiCall | 12036-12091 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/pulls` | Raw HTTP / custom ApiCall | 12092-12194 |
| `POST /manage/v2/databases/{id&#124;name}/flexrep/pulls` | Raw HTTP / custom ApiCall | 12195-12312 |
| `DELETE /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}` | Raw HTTP / custom ApiCall | 12313-12349 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}` | Raw HTTP / custom ApiCall | 12350-12476 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 12477-12573 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 12574-12668 |
| `GET /manage/v2/databases/{id&#124;name}/partition-queries` | Raw HTTP / custom ApiCall | 12669-12814 |
| `POST /manage/v2/databases/{id&#124;name}/partition-queries` | Raw HTTP / custom ApiCall | 12815-12929 |
| `DELETE /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}` | Raw HTTP / custom ApiCall | 12930-12965 |
| `GET /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}` | Raw HTTP / custom ApiCall | 12966-13009 |
| `GET /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}/properties` | Raw HTTP / custom ApiCall | 13010-13054 |
| `PUT /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}/properties` | Raw HTTP / custom ApiCall | 13055-13097 |
| `GET /manage/v2/databases/{id&#124;name}/partitions` | Raw HTTP / custom ApiCall | 13098-13243 |
| `POST /manage/v2/databases/{id&#124;name}/partitions` | Raw HTTP / custom ApiCall | 13244-13422 |
| `DELETE /manage/v2/databases/{id&#124;name}/partitions/{name}` | Raw HTTP / custom ApiCall | 13423-13467 |
| `GET /manage/v2/databases/{id&#124;name}/partitions/{name}` | Raw HTTP / custom ApiCall | 13468-13640 |
| `PUT /manage/v2/databases/{id&#124;name}/partitions/{name}` | Raw HTTP / custom ApiCall | 13641-13849 |
| `GET /manage/v2/databases/{id&#124;name}/partitions/{name}/properties` | Raw HTTP / custom ApiCall | 13850-13903 |
| `PUT /manage/v2/databases/{id&#124;name}/partitions/{name}/properties` | Raw HTTP / custom ApiCall | 13904-13986 |
| `GET /manage/v2/databases/{id&#124;name}/pipelines` | Raw HTTP / custom ApiCall | 13987-14090 |
| `POST /manage/v2/databases/{id&#124;name}/pipelines` | Raw HTTP / custom ApiCall | 14091-14274 |
| `DELETE /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}` | Raw HTTP / custom ApiCall | 14275-14311 |
| `GET /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}` | Raw HTTP / custom ApiCall | 14312-14440 |
| `GET /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 14441-14570 |
| `PUT /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 14571-14697 |
| `GET /manage/v2/databases/{id&#124;name}/properties` | `ml.manage.databases.get_properties` (sync and async) | 14698-15609 |
| `PUT /manage/v2/databases/{id&#124;name}/properties` | `ml.manage.databases.put_properties` (sync and async) | 15610-16576 |
| `GET /manage/v2/databases/{id&#124;name}/rebalancer` | Raw HTTP / custom ApiCall | 16577-16663 |
| `PUT /manage/v2/databases/{id&#124;name}/rebalancer` | Raw HTTP / custom ApiCall | 16664-16733 |
| `GET /manage/v2/databases/{id&#124;name}/temporal` | Raw HTTP / custom ApiCall | 16734-16851 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/axes` | Raw HTTP / custom ApiCall | 16852-16944 |
| `POST /manage/v2/databases/{id&#124;name}/temporal/axes` | Raw HTTP / custom ApiCall | 16945-17029 |
| `DELETE /manage/v2/databases/{id&#124;name}/temporal/axes/{id&#124;name}` | Raw HTTP / custom ApiCall | 17030-17070 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/axes/{id&#124;name}` | Raw HTTP / custom ApiCall | 17071-17195 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/axes/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 17196-17253 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections` | Raw HTTP / custom ApiCall | 17254-17352 |
| `POST /manage/v2/databases/{id&#124;name}/temporal/collections` | Raw HTTP / custom ApiCall | 17353-17430 |
| `DELETE /manage/v2/databases/{id&#124;name}/temporal/collections?collection={name}` | Raw HTTP / custom ApiCall | 17431-17474 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections?collection={name}` | Raw HTTP / custom ApiCall | 17475-17600 |
| `POST /manage/v2/databases/{id&#124;name}/temporal/collections?collection={name}` | Raw HTTP / custom ApiCall | 17601-17687 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections/lsqt/properties?collection={name}` | Raw HTTP / custom ApiCall | 17688-17742 |
| `PUT /manage/v2/databases/{id&#124;name}/temporal/collections/lsqt/properties?collection={name}` | Raw HTTP / custom ApiCall | 17743-17806 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections/properties?collection={name}` | Raw HTTP / custom ApiCall | 17807-17868 |
| `PUT /manage/v2/databases/{id&#124;name}/temporal/collections/properties?collection={name}` | Raw HTTP / custom ApiCall | 17869-17927 |
| `GET /manage/v2/databases/{id&#124;name}/triggers` | Raw HTTP / custom ApiCall | 17928-18027 |
| `POST /manage/v2/databases/{id&#124;name}/triggers` | Raw HTTP / custom ApiCall | 18028-18174 |
| `DELETE /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}` | Raw HTTP / custom ApiCall | 18175-18215 |
| `GET /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}` | Raw HTTP / custom ApiCall | 18216-18338 |
| `GET /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 18339-18460 |
| `PUT /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 18461-18587 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas` | Raw HTTP / custom ApiCall | 18588-18688 |
| `POST /manage/v2/databases/{id&#124;name}/view-schemas` | Raw HTTP / custom ApiCall | 18689-18755 |
| `DELETE /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}` | Raw HTTP / custom ApiCall | 18756-18794 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}` | Raw HTTP / custom ApiCall | 18795-18920 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 18921-18983 |
| `PUT /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 18984-19051 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views` | Raw HTTP / custom ApiCall | 19052-19152 |
| `POST /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views` | Raw HTTP / custom ApiCall | 19153-19318 |
| `DELETE /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}` | Raw HTTP / custom ApiCall | 19319-19357 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}` | Raw HTTP / custom ApiCall | 19358-19483 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 19484-19570 |
| `PUT /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 19571-19660 |
| `GET /manage/v2/external-security` | Raw HTTP / custom ApiCall | 19661-19758 |
| `POST /manage/v2/external-security` | Raw HTTP / custom ApiCall | 19759-19987 |
| `DELETE /manage/v2/external-security/{id&#124;name}` | Raw HTTP / custom ApiCall | 19988-20029 |
| `GET /manage/v2/external-security/{id&#124;name}` | Raw HTTP / custom ApiCall | 20030-20179 |
| `GET /manage/v2/external-security/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 20180-20388 |
| `PUT /manage/v2/external-security/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 20389-20600 |
| `GET /manage/v2/forests` | `ml.manage.forests.get_list` (sync and async) | 20601-20748 |
| `POST /manage/v2/forests` | `ml.manage.forests.create` (sync and async) | 20749-20953 |
| `PUT /manage/v2/forests` | `ml.manage.forests.put` (sync and async) | 20954-21170 |
| `GET /manage/v2/forests?view=metrics` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 21171-21225 |
| `GET /manage/v2/forests?view=status` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 21226-21662 |
| `GET /manage/v2/forests?view=storage` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 21663-21873 |
| `DELETE /manage/v2/forests/{id&#124;name}` | `ml.manage.forests.delete` (sync and async) | 21874-21917 |
| `GET /manage/v2/forests/{id&#124;name}` | `ml.manage.forests.get` (sync and async) | 21918-22061 |
| `POST /manage/v2/forests/{id&#124;name}` | `ml.manage.forests.post` (sync and async) | 22062-22212 |
| `GET /manage/v2/forests/{id&#124;name}?view=counts` | `ml.manage.forests.get` (sync and async); pass the documented query parameter (check wrapper validation) | 22213-22809 |
| `GET /manage/v2/forests/{id&#124;name}?view=status` | `ml.manage.forests.get` (sync and async); pass the documented query parameter (check wrapper validation) | 22810-23556 |
| `GET /manage/v2/forests/{id&#124;name}/properties` | `ml.manage.forests.get_properties` (sync and async) | 23557-23737 |
| `PUT /manage/v2/forests/{id&#124;name}/properties` | `ml.manage.forests.put_properties` (sync and async) | 23738-23916 |
| `GET /manage/v2/groups` | Raw HTTP / custom ApiCall | 23917-24052 |
| `POST /manage/v2/groups` | Raw HTTP / custom ApiCall | 24053-24291 |
| `DELETE /manage/v2/groups/{id&#124;name}` | Raw HTTP / custom ApiCall | 24292-24329 |
| `GET /manage/v2/groups/{id&#124;name}` | Raw HTTP / custom ApiCall | 24330-24473 |
| `POST /manage/v2/groups/{id&#124;name}` | Raw HTTP / custom ApiCall | 24474-24531 |
| `GET /manage/v2/groups/{id&#124;name}?view=counts` | Raw HTTP / custom ApiCall | 24532-24630 |
| `GET /manage/v2/groups/{id&#124;name}?view=status` | Raw HTTP / custom ApiCall | 24631-25221 |
| `GET /manage/v2/groups/{id&#124;name}/properties` | `ml.manage.groups.get_properties` (sync and async) | 25222-25465 |
| `PUT /manage/v2/groups/{id&#124;name}/properties` | `ml.manage.groups.put_properties` (sync and async) | 25466-25706 |
| `GET /manage/v2/hosts` | `ml.manage.hosts.get_list` (sync and async) | 25707-25850 |
| `POST /manage/v2/hosts` | Raw HTTP / custom ApiCall | 25851-25932 |
| `GET /manage/v2/hosts?view=metrics` | `ml.manage.hosts.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 25933-25987 |
| `GET /manage/v2/hosts?view=status` | `ml.manage.hosts.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 25988-26508 |
| `GET /manage/v2/hosts/{id&#124;name}` | Raw HTTP / custom ApiCall | 26509-26652 |
| `POST /manage/v2/hosts/{id&#124;name}` | Raw HTTP / custom ApiCall | 26653-26789 |
| `GET /manage/v2/hosts/{id&#124;name}?view=config` | Raw HTTP / custom ApiCall | 26790-26896 |
| `GET /manage/v2/hosts/{id&#124;name}?view=counts` | Raw HTTP / custom ApiCall | 26897-26995 |
| `GET /manage/v2/hosts/{id&#124;name}?view=status` | Raw HTTP / custom ApiCall | 26996-28482 |
| `GET /manage/v2/hosts/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 28483-28578 |
| `PUT /manage/v2/hosts/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 28579-28687 |
| `GET /manage/v2/logs` | `ml.manage.logs.get` (sync and async) | 28688-28736 |
| `GET /manage/v2/meters` | Raw HTTP / custom ApiCall | 28737-28795 |
| `GET /manage/v2/meters/labels` | Raw HTTP / custom ApiCall | 28796-28847 |
| `OPTIONS /manage/v2/meters/labels` | Raw HTTP / custom ApiCall | 28848-28888 |
| `POST /manage/v2/meters/labels` | Raw HTTP / custom ApiCall | 28889-28951 |
| `DELETE /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 28952-28974 |
| `GET /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 28975-29023 |
| `HEAD /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 29024-29047 |
| `OPTIONS /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 29048-29092 |
| `PUT /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 29093-29154 |
| `GET /manage/v2/meters/resources` | Raw HTTP / custom ApiCall | 29155-29273 |
| `GET /manage/v2/mimetypes` | Raw HTTP / custom ApiCall | 29274-29406 |
| `POST /manage/v2/mimetypes` | Raw HTTP / custom ApiCall | 29407-29557 |
| `DELETE /manage/v2/mimetypes/{id&#124;name}` | Raw HTTP / custom ApiCall | 29558-29596 |
| `GET /manage/v2/mimetypes/{id&#124;name}` | Raw HTTP / custom ApiCall | 29597-29721 |
| `GET /manage/v2/mimetypes/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 29722-29805 |
| `PUT /manage/v2/mimetypes/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 29806-29890 |
| `GET /manage/v2/privileges` | Raw HTTP / custom ApiCall | 29891-29987 |
| `POST /manage/v2/privileges` | Raw HTTP / custom ApiCall | 29988-30056 |
| `DELETE /manage/v2/privileges/{id&#124;name}` | Raw HTTP / custom ApiCall | 30057-30098 |
| `GET /manage/v2/privileges/{id&#124;name}` | Raw HTTP / custom ApiCall | 30099-30229 |
| `GET /manage/v2/privileges/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 30230-30291 |
| `PUT /manage/v2/privileges/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 30292-30360 |
| `GET /manage/v2/properties` | Raw HTTP / custom ApiCall | 30361-30452 |
| `PUT /manage/v2/properties` | Raw HTTP / custom ApiCall | 30453-30553 |
| `GET /manage/v2/protected-collections` | Raw HTTP / custom ApiCall | 30554-30650 |
| `POST /manage/v2/protected-collections` | Raw HTTP / custom ApiCall | 30651-30730 |
| `DELETE /manage/v2/protected-collections?collection={collection-uri}` | Raw HTTP / custom ApiCall | 30731-30773 |
| `GET /manage/v2/protected-collections?collection={collection-uri}` | Raw HTTP / custom ApiCall | 30774-30835 |
| `GET /manage/v2/protected-collections/properties?collection={collection-uri}` | Raw HTTP / custom ApiCall | 30836-30898 |
| `PUT /manage/v2/protected-collections/properties?collection={collection-uri}` | Raw HTTP / custom ApiCall | 30899-30967 |
| `GET /manage/v2/protected-paths` | Raw HTTP / custom ApiCall | 30968-31141 |
| `POST /manage/v2/protected-paths` | Raw HTTP / custom ApiCall | 31142-31256 |
| `GET /manage/v2/protected-paths/{id}/properties` | Raw HTTP / custom ApiCall | 31257-31375 |
| `PUT /manage/v2/protected-paths/{id}/properties` | Raw HTTP / custom ApiCall | 31376-31485 |
| `DELETE /manage/v2/protected-paths/{id&#124;name}` | Raw HTTP / custom ApiCall | 31486-31537 |
| `GET /manage/v2/protected-paths/{id&#124;name}` | Raw HTTP / custom ApiCall | 31538-31735 |
| `GET /manage/v2/query-rolesets` | Raw HTTP / custom ApiCall | 31736-31865 |
| `POST /manage/v2/query-rolesets` | Raw HTTP / custom ApiCall | 31866-31935 |
| `DELETE /manage/v2/query-rolesets/{id}` | Raw HTTP / custom ApiCall | 31936-31976 |
| `GET /manage/v2/query-rolesets/{id}` | Raw HTTP / custom ApiCall | 31977-32095 |
| `GET /manage/v2/query-rolesets/{id}/properties` | Raw HTTP / custom ApiCall | 32096-32189 |
| `GET /manage/v2/requests` | Raw HTTP / custom ApiCall | 32190-32457 |
| `GET /manage/v2/requests/{id&#124;uri}` | Raw HTTP / custom ApiCall | 32458-32639 |
| `GET /manage/v2/roles` | `ml.manage.roles.get_list` (sync and async) | 32640-32735 |
| `POST /manage/v2/roles` | `ml.manage.roles.create` (sync and async) | 32736-32911 |
| `DELETE /manage/v2/roles/{id&#124;name}` | `ml.manage.roles.delete` (sync and async) | 32912-32952 |
| `GET /manage/v2/roles/{id&#124;name}` | `ml.manage.roles.get` (sync and async) | 32953-33081 |
| `GET /manage/v2/roles/{id&#124;name}/properties` | `ml.manage.roles.get_properties` (sync and async) | 33082-33207 |
| `PUT /manage/v2/roles/{id&#124;name}/properties` | `ml.manage.roles.put_properties` (sync and async) | 33208-33383 |
| `GET /manage/v2/security` | Raw HTTP / custom ApiCall | 33384-33467 |
| `POST /manage/v2/security` | Raw HTTP / custom ApiCall | 33468-33519 |
| `GET /manage/v2/security/properties` | Raw HTTP / custom ApiCall | 33520-33696 |
| `PUT /manage/v2/security/properties` | Raw HTTP / custom ApiCall | 33697-33823 |
| `GET /manage/v2/servers` | `ml.manage.servers.get_list` (sync and async) | 33824-34006 |
| `POST /manage/v2/servers` | `ml.manage.servers.create` (sync and async) | 34007-34837 |
| `GET /manage/v2/servers?view=metrics` | `ml.manage.servers.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 34838-34893 |
| `GET /manage/v2/servers?view=status` | `ml.manage.servers.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 34894-35075 |
| `GET /manage/v2/servers?view=xdmp:server-status` | `ml.manage.servers.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 35076-35380 |
| `DELETE /manage/v2/servers/{id&#124;name}` | `ml.manage.servers.delete` (sync and async) | 35381-35422 |
| `GET /manage/v2/servers/{id&#124;name}` | `ml.manage.servers.get` (sync and async) | 35423-36684 |
| `GET /manage/v2/servers/{id&#124;name}?view=package` | `ml.manage.servers.get` (sync and async); pass the documented query parameter (check wrapper validation) | 36685-36732 |
| `GET /manage/v2/servers/{id&#124;name}?view=status` | `ml.manage.servers.get` (sync and async); pass the documented query parameter (check wrapper validation) | 36733-37138 |
| `GET /manage/v2/servers/{id&#124;name}/properties` | `ml.manage.servers.get_properties` (sync and async) | 37139-37938 |
| `PUT /manage/v2/servers/{id&#124;name}/properties` | `ml.manage.servers.put_properties` (sync and async) | 37939-38743 |
| `GET /manage/v2/support-request` | Raw HTTP / custom ApiCall | 38744-38787 |
| `GET /manage/v2/task-servers` | Raw HTTP / custom ApiCall | 38788-38830 |
| `GET /manage/v2/task-servers/{id&#124;name}` | Raw HTTP / custom ApiCall | 38831-38873 |
| `GET /manage/v2/task-servers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 38874-39017 |
| `PUT /manage/v2/task-servers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 39018-39161 |
| `GET /manage/v2/tasks` | Raw HTTP / custom ApiCall | 39162-39244 |
| `POST /manage/v2/tasks` | Raw HTTP / custom ApiCall | 39245-39355 |
| `DELETE /manage/v2/tasks/{id}` | Raw HTTP / custom ApiCall | 39356-39395 |
| `GET /manage/v2/tasks/{id}` | Raw HTTP / custom ApiCall | 39396-39498 |
| `GET /manage/v2/tasks/{id}/properties` | Raw HTTP / custom ApiCall | 39499-39604 |
| `PUT /manage/v2/tasks/{id}/properties` | Raw HTTP / custom ApiCall | 39605-39721 |
| `GET /manage/v2/tickets/{tid}?view=process-status` | Raw HTTP / custom ApiCall | 39722-39836 |
| `GET /manage/v2/transactions` | Raw HTTP / custom ApiCall | 39837-40068 |
| `GET /manage/v2/transactions/{id&#124;uri}` | Raw HTTP / custom ApiCall | 40069-40228 |
| `GET /manage/v2/usage-report` | Raw HTTP / custom ApiCall | 40229-40277 |
| `GET /manage/v2/users` | `ml.manage.users.get_list` (sync and async) | 40278-40373 |
| `POST /manage/v2/users` | `ml.manage.users.create` (sync and async) | 40374-40542 |
| `DELETE /manage/v2/users/{id&#124;name}` | `ml.manage.users.delete` (sync and async) | 40543-40583 |
| `GET /manage/v2/users/{id&#124;name}` | `ml.manage.users.get` (sync and async) | 40584-40710 |
| `GET /manage/v2/users/{id&#124;name}/properties` | `ml.manage.users.get_properties` (sync and async) | 40711-40825 |
| `PUT /manage/v2/users/{id&#124;name}/properties` | `ml.manage.users.put_properties` (sync and async) | 40826-40989 |
| `GET /manage/v3` | Raw HTTP / custom ApiCall | 40990-41136 |
| `POST /manage/v3` | Raw HTTP / custom ApiCall | 41137-41285 |
| `GET /v1/alert/match` | Raw HTTP / custom ApiCall | 41286-41424 |
| `POST /v1/alert/match` | Raw HTTP / custom ApiCall | 41425-41586 |
| `GET /v1/alert/rules` | Raw HTTP / custom ApiCall | 41587-41696 |
| `DELETE /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 41697-41737 |
| `GET /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 41738-41845 |
| `HEAD /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 41846-41899 |
| `PUT /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 41900-42002 |
| `GET /v1/config/indexes` | Raw HTTP / custom ApiCall | 42003-42103 |
| `GET /v1/config/indexes/{name}` | Raw HTTP / custom ApiCall | 42104-42197 |
| `DELETE /v1/config/namespaces` | Raw HTTP / custom ApiCall | 42198-42239 |
| `GET /v1/config/namespaces` | Raw HTTP / custom ApiCall | 42240-42351 |
| `POST /v1/config/namespaces` | Raw HTTP / custom ApiCall | 42352-42465 |
| `PUT /v1/config/namespaces` | Raw HTTP / custom ApiCall | 42466-42579 |
| `DELETE /v1/config/namespaces/{prefix}` | Raw HTTP / custom ApiCall | 42580-42622 |
| `GET /v1/config/namespaces/{prefix}` | Raw HTTP / custom ApiCall | 42623-42721 |
| `PUT /v1/config/namespaces/{prefix}` | Raw HTTP / custom ApiCall | 42722-42819 |
| `DELETE /v1/config/properties` | Raw HTTP / custom ApiCall | 42820-42852 |
| `GET /v1/config/properties` | Raw HTTP / custom ApiCall | 42853-42946 |
| `PUT /v1/config/properties` | Raw HTTP / custom ApiCall | 42947-43023 |
| `DELETE /v1/config/properties/{property-name}` | Raw HTTP / custom ApiCall | 43024-43054 |
| `GET /v1/config/properties/{property-name}` | Raw HTTP / custom ApiCall | 43055-43151 |
| `PUT /v1/config/properties/{property-name}` | Raw HTTP / custom ApiCall | 43152-43225 |
| `DELETE /v1/config/query` | Raw HTTP / custom ApiCall | 43226-43264 |
| `GET /v1/config/query` | Raw HTTP / custom ApiCall | 43265-43382 |
| `DELETE /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 43383-43422 |
| `GET /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 43423-43556 |
| `POST /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 43557-43641 |
| `PUT /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 43642-43742 |
| `DELETE /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 43743-43772 |
| `GET /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 43773-43932 |
| `POST /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 43933-44055 |
| `PUT /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 44056-44185 |
| `GET /v1/config/resources` | Raw HTTP / custom ApiCall | 44186-44334 |
| `DELETE /v1/config/resources/{name}` | Raw HTTP / custom ApiCall | 44335-44374 |
| `GET /v1/config/resources/{name}` | Raw HTTP / custom ApiCall | 44375-44435 |
| `PUT /v1/config/resources/{name}` | Raw HTTP / custom ApiCall | 44436-44539 |
| `POST /v1/config/server` | Raw HTTP / custom ApiCall | 44540-44635 |
| `GET /v1/config/transforms` | Raw HTTP / custom ApiCall | 44636-44775 |
| `DELETE /v1/config/transforms/{name}` | Raw HTTP / custom ApiCall | 44776-44815 |
| `GET /v1/config/transforms/{name}` | Raw HTTP / custom ApiCall | 44816-44881 |
| `PUT /v1/config/transforms/{name}` | Raw HTTP / custom ApiCall | 44882-44980 |
| `DELETE /v1/documents` | `ml.rest.documents.delete` (sync and async) | 44981-45085 |
| `GET /v1/documents` | `ml.rest.documents.get` (sync and async) | 45086-45360 |
| `HEAD /v1/documents` | Raw HTTP / custom ApiCall | 45361-45420 |
| `PATCH /v1/documents` | Raw HTTP / custom ApiCall | 45421-45557 |
| `POST /v1/documents` | `ml.rest.documents.post` (sync and async) | 45558-45783 |
| `PUT /v1/documents` | Raw HTTP / custom ApiCall | 45784-45948 |
| `POST /v1/documents?extension={ext}` | `ml.rest.documents.post` (sync and async); pass the documented query parameter (check wrapper validation) | 45949-46091 |
| `POST /v1/documents?uri={db-uri}` | `ml.rest.documents.post` (sync and async); pass the documented query parameter (check wrapper validation) | 46092-46235 |
| `POST /v1/documents/protection` | Raw HTTP / custom ApiCall | 46236-46399 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/status` | Raw HTTP / custom ApiCall | 46400-46469 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets` | Raw HTTP / custom ApiCall | 46470-46540 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}` | Raw HTTP / custom ApiCall | 46541-46578 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 46579-46646 |
| `POST /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 46647-46694 |
| `DELETE /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules/ALERT_ID` | Raw HTTP / custom ApiCall | 46695-46736 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules/ALERT_ID` | Raw HTTP / custom ApiCall | 46737-46773 |
| `PUT /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules/ALERT_ID` | Raw HTTP / custom ApiCall | 46774-46811 |
| `POST /v1/eval` | `ml.rest.eval.post` (sync and async) | 46812-46969 |
| `DELETE /v1/ext/{directories}` | Raw HTTP / custom ApiCall | 46970-47013 |
| `GET /v1/ext/{directories}` | Raw HTTP / custom ApiCall | 47014-47128 |
| `DELETE /v1/ext/{directories}/{asset}` | Raw HTTP / custom ApiCall | 47129-47176 |
| `GET /v1/ext/{directories}/{asset}` | Raw HTTP / custom ApiCall | 47177-47245 |
| `PUT /v1/ext/{directories}/{asset}` | Raw HTTP / custom ApiCall | 47246-47320 |
| `DELETE /v1/graphs` | Raw HTTP / custom ApiCall | 47321-47431 |
| `GET /v1/graphs` | Raw HTTP / custom ApiCall | 47432-47608 |
| `HEAD /v1/graphs` | Raw HTTP / custom ApiCall | 47609-47663 |
| `POST /v1/graphs` | Raw HTTP / custom ApiCall | 47664-47828 |
| `PUT /v1/graphs` | Raw HTTP / custom ApiCall | 47829-47978 |
| `GET /v1/graphs/sparql` | Raw HTTP / custom ApiCall | 47979-48127 |
| `POST /v1/graphs/sparql` | Raw HTTP / custom ApiCall | 48128-48433 |
| `GET /v1/graphs/things` | Raw HTTP / custom ApiCall | 48434-48564 |
| `POST /v1/invoke` | Raw HTTP / custom ApiCall | 48565-48743 |
| `GET /v1/qbe` | Raw HTTP / custom ApiCall | 48744-49018 |
| `POST /v1/qbe` | Raw HTTP / custom ApiCall | 49019-49306 |
| `DELETE /v1/resources/{name}` | Raw HTTP / custom ApiCall | 49307-49359 |
| `GET /v1/resources/{name}` | Raw HTTP / custom ApiCall | 49360-49407 |
| `POST /v1/resources/{name}` | Raw HTTP / custom ApiCall | 49408-49461 |
| `PUT /v1/resources/{name}` | Raw HTTP / custom ApiCall | 49462-49514 |
| `GET /v1/rest-apis` | Raw HTTP / custom ApiCall | 49515-49613 |
| `POST /v1/rest-apis` | Raw HTTP / custom ApiCall | 49614-49717 |
| `DELETE /v1/rest-apis/{name}` | Raw HTTP / custom ApiCall | 49718-49797 |
| `GET /v1/rest-apis/{name}` | Raw HTTP / custom ApiCall | 49798-49907 |
| `GET /v1/rows` | Raw HTTP / custom ApiCall | 49908-50180 |
| `POST /v1/rows` | Raw HTTP / custom ApiCall | 50181-50476 |
| `DELETE /v1/search` | Raw HTTP / custom ApiCall | 50477-50523 |
| `GET /v1/search` | Raw HTTP / custom ApiCall | 50524-50874 |
| `POST /v1/search` | Raw HTTP / custom ApiCall | 50875-51281 |
| `GET /v1/suggest` | Raw HTTP / custom ApiCall | 51282-51420 |
| `POST /v1/suggest` | Raw HTTP / custom ApiCall | 51421-51606 |
| `POST /v1/temporal/collections/{name}` | Raw HTTP / custom ApiCall | 51607-51666 |
| `POST /v1/transactions` | `ml.rest.transactions.create` (sync and async) | 51667-51742 |
| `GET /v1/transactions/{txid}` | `ml.rest.transactions.get` (sync and async) | 51743-51887 |
| `POST /v1/transactions/{txid}` | `ml.rest.transactions.post` (sync and async) | 51888-51946 |
| `GET /v1/values` | Raw HTTP / custom ApiCall | 51947-52091 |
| `GET /v1/values/{name}` | Raw HTTP / custom ApiCall | 52092-52274 |
| `POST /v1/values/{name}` | Raw HTTP / custom ApiCall | 52275-52648 |
