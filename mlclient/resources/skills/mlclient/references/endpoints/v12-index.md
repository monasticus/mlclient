# MarkLogic 12: 406 endpoint contracts

Read only the relevant section of `v12.md`, using the inclusive line ranges below.
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
| `GET /manage/v2?view=healthcheck` | Raw HTTP / custom ApiCall | 1195-1479 |
| `GET /manage/v2?view=query` | Raw HTTP / custom ApiCall | 1480-1617 |
| `GET /manage/v2?view=status` | Raw HTTP / custom ApiCall | 1618-2405 |
| `GET /manage/v2/amps` | Raw HTTP / custom ApiCall | 2406-2511 |
| `POST /manage/v2/amps` | Raw HTTP / custom ApiCall | 2512-2592 |
| `DELETE /manage/v2/amps/{id&#124;name}` | Raw HTTP / custom ApiCall | 2593-2637 |
| `GET /manage/v2/amps/{id&#124;name}` | Raw HTTP / custom ApiCall | 2638-2774 |
| `GET /manage/v2/amps/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 2775-2839 |
| `PUT /manage/v2/amps/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 2840-2908 |
| `GET /manage/v2/certificate-authorities` | Raw HTTP / custom ApiCall | 2909-3011 |
| `POST /manage/v2/certificate-authorities` | Raw HTTP / custom ApiCall | 3012-3132 |
| `DELETE /manage/v2/certificate-authorities/{id&#124;name}` | Raw HTTP / custom ApiCall | 3133-3174 |
| `GET /manage/v2/certificate-authorities/{id&#124;name}` | Raw HTTP / custom ApiCall | 3175-3227 |
| `GET /manage/v2/certificate-authorities/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 3228-3281 |
| `PUT /manage/v2/certificate-revocation-lists` | Raw HTTP / custom ApiCall | 3282-3324 |
| `GET /manage/v2/certificate-templates` | Raw HTTP / custom ApiCall | 3325-3433 |
| `POST /manage/v2/certificate-templates` | Raw HTTP / custom ApiCall | 3434-3569 |
| `DELETE /manage/v2/certificate-templates/{id&#124;name}` | Raw HTTP / custom ApiCall | 3570-3610 |
| `GET /manage/v2/certificate-templates/{id&#124;name}` | Raw HTTP / custom ApiCall | 3611-3739 |
| `POST /manage/v2/certificate-templates/{id&#124;name}` | Raw HTTP / custom ApiCall | 3740-3859 |
| `GET /manage/v2/certificate-templates/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 3860-3971 |
| `PUT /manage/v2/certificate-templates/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 3972-4083 |
| `GET /manage/v2/certificates` | Raw HTTP / custom ApiCall | 4084-4185 |
| `POST /manage/v2/certificates` | Raw HTTP / custom ApiCall | 4186-4264 |
| `DELETE /manage/v2/certificates/{id&#124;name}` | Raw HTTP / custom ApiCall | 4265-4304 |
| `GET /manage/v2/certificates/{id&#124;name}` | Raw HTTP / custom ApiCall | 4305-4428 |
| `GET /manage/v2/certificates/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 4429-4548 |
| `GET /manage/v2/clusters` | Raw HTTP / custom ApiCall | 4549-4685 |
| `POST /manage/v2/clusters` | Raw HTTP / custom ApiCall | 4686-4833 |
| `GET /manage/v2/clusters?view=metrics` | Raw HTTP / custom ApiCall | 4834-4891 |
| `DELETE /manage/v2/clusters/{id&#124;name}` | Raw HTTP / custom ApiCall | 4892-4935 |
| `GET /manage/v2/clusters/{id&#124;name}` | Raw HTTP / custom ApiCall | 4936-5066 |
| `POST /manage/v2/clusters/{id&#124;name}` | Raw HTTP / custom ApiCall | 5067-5283 |
| `GET /manage/v2/clusters/{id&#124;name}?view=metrics` | Raw HTTP / custom ApiCall | 5284-5337 |
| `GET /manage/v2/clusters/{id&#124;name}?view=status` | Raw HTTP / custom ApiCall | 5338-5512 |
| `DELETE /manage/v2/clusters/{id&#124;name}/dynamic-host-token` | Raw HTTP / custom ApiCall | 5513-5556 |
| `GET /manage/v2/clusters/{id&#124;name}/dynamic-host-token` | Raw HTTP / custom ApiCall | 5557-5601 |
| `POST /manage/v2/clusters/{id&#124;name}/dynamic-host-token` | Raw HTTP / custom ApiCall | 5602-5647 |
| `DELETE /manage/v2/clusters/{id&#124;name}/dynamic-hosts` | Raw HTTP / custom ApiCall | 5648-5692 |
| `GET /manage/v2/clusters/{id&#124;name}/dynamic-hosts` | Raw HTTP / custom ApiCall | 5693-5732 |
| `GET /manage/v2/clusters/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 5733-5812 |
| `PUT /manage/v2/clusters/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 5813-5900 |
| `DELETE /manage/v2/credentials/properties` | Raw HTTP / custom ApiCall | 5901-5942 |
| `GET /manage/v2/credentials/properties` | Raw HTTP / custom ApiCall | 5943-6008 |
| `PUT /manage/v2/credentials/properties` | Raw HTTP / custom ApiCall | 6009-6081 |
| `GET /manage/v2/credentials/secure` | Raw HTTP / custom ApiCall | 6082-6174 |
| `POST /manage/v2/credentials/secure` | Raw HTTP / custom ApiCall | 6175-6305 |
| `GET /manage/v2/databases` | `ml.manage.databases.get_list` (sync and async) | 6306-6439 |
| `POST /manage/v2/databases` | `ml.manage.databases.create` (sync and async) | 6440-7375 |
| `GET /manage/v2/databases?view=metrics` | `ml.manage.databases.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 7376-7429 |
| `DELETE /manage/v2/databases/{id&#124;name}` | `ml.manage.databases.delete` (sync and async) | 7430-7478 |
| `GET /manage/v2/databases/{id&#124;name}` | `ml.manage.databases.get` (sync and async) | 7479-7614 |
| `POST /manage/v2/databases/{id&#124;name}` | `ml.manage.databases.post` (sync and async) | 7615-8024 |
| `GET /manage/v2/databases/{id&#124;name}?view=counts` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 8025-8126 |
| `GET /manage/v2/databases/{id&#124;name}?view=describe-indexes` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 8127-8218 |
| `GET /manage/v2/databases/{id&#124;name}?view=package` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 8219-8265 |
| `GET /manage/v2/databases/{id&#124;name}?view=status` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 8266-8803 |
| `GET /manage/v2/databases/{id&#124;name}/alert` | Raw HTTP / custom ApiCall | 8804-8922 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions` | Raw HTTP / custom ApiCall | 8923-9014 |
| `POST /manage/v2/databases/{id&#124;name}/alert/actions` | Raw HTTP / custom ApiCall | 9015-9093 |
| `DELETE /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}` | Raw HTTP / custom ApiCall | 9094-9136 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}` | Raw HTTP / custom ApiCall | 9137-9259 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 9260-9324 |
| `PUT /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 9325-9397 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 9398-9488 |
| `POST /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 9489-9668 |
| `DELETE /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}` | Raw HTTP / custom ApiCall | 9669-9711 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}` | Raw HTTP / custom ApiCall | 9712-9832 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 9833-9901 |
| `PUT /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 9902-10067 |
| `DELETE /manage/v2/databases/{id&#124;name}/alert/configs` | Raw HTTP / custom ApiCall | 10068-10112 |
| `GET /manage/v2/databases/{id&#124;name}/alert/configs` | Raw HTTP / custom ApiCall | 10113-10243 |
| `POST /manage/v2/databases/{id&#124;name}/alert/configs` | Raw HTTP / custom ApiCall | 10244-10355 |
| `GET /manage/v2/databases/{id&#124;name}/alert/configs/properties` | Raw HTTP / custom ApiCall | 10356-10432 |
| `PUT /manage/v2/databases/{id&#124;name}/alert/configs/properties` | Raw HTTP / custom ApiCall | 10433-10520 |
| `GET /manage/v2/databases/{id&#124;name}/cpf-configs` | Raw HTTP / custom ApiCall | 10521-10622 |
| `POST /manage/v2/databases/{id&#124;name}/cpf-configs` | Raw HTTP / custom ApiCall | 10623-10735 |
| `DELETE /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}` | Raw HTTP / custom ApiCall | 10736-10772 |
| `GET /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}` | Raw HTTP / custom ApiCall | 10773-10897 |
| `GET /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}/properties` | Raw HTTP / custom ApiCall | 10898-10965 |
| `PUT /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}/properties` | Raw HTTP / custom ApiCall | 10966-11036 |
| `GET /manage/v2/databases/{id&#124;name}/domains` | Raw HTTP / custom ApiCall | 11037-11140 |
| `POST /manage/v2/databases/{id&#124;name}/domains` | Raw HTTP / custom ApiCall | 11141-11234 |
| `DELETE /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}` | Raw HTTP / custom ApiCall | 11235-11271 |
| `GET /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}` | Raw HTTP / custom ApiCall | 11272-11396 |
| `GET /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 11397-11474 |
| `PUT /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 11475-11553 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep` | Raw HTTP / custom ApiCall | 11554-11675 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs` | Raw HTTP / custom ApiCall | 11676-11777 |
| `POST /manage/v2/databases/{id&#124;name}/flexrep/configs` | Raw HTTP / custom ApiCall | 11778-11834 |
| `DELETE /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}` | Raw HTTP / custom ApiCall | 11835-11872 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}` | Raw HTTP / custom ApiCall | 11873-11999 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 12000-12054 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 12055-12108 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets` | Raw HTTP / custom ApiCall | 12109-12211 |
| `POST /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets` | Raw HTTP / custom ApiCall | 12212-12362 |
| `DELETE /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}` | Raw HTTP / custom ApiCall | 12363-12401 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}` | Raw HTTP / custom ApiCall | 12402-12528 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 12529-12647 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 12648-12769 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/properties` | Raw HTTP / custom ApiCall | 12770-12825 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/properties` | Raw HTTP / custom ApiCall | 12826-12881 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/pulls` | Raw HTTP / custom ApiCall | 12882-12984 |
| `POST /manage/v2/databases/{id&#124;name}/flexrep/pulls` | Raw HTTP / custom ApiCall | 12985-13102 |
| `DELETE /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}` | Raw HTTP / custom ApiCall | 13103-13139 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}` | Raw HTTP / custom ApiCall | 13140-13266 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 13267-13363 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 13364-13458 |
| `GET /manage/v2/databases/{id&#124;name}/partition-queries` | Raw HTTP / custom ApiCall | 13459-13604 |
| `POST /manage/v2/databases/{id&#124;name}/partition-queries` | Raw HTTP / custom ApiCall | 13605-13729 |
| `DELETE /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}` | Raw HTTP / custom ApiCall | 13730-13765 |
| `GET /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}` | Raw HTTP / custom ApiCall | 13766-13809 |
| `GET /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}/properties` | Raw HTTP / custom ApiCall | 13810-13863 |
| `PUT /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}/properties` | Raw HTTP / custom ApiCall | 13864-13962 |
| `GET /manage/v2/databases/{id&#124;name}/partitions` | Raw HTTP / custom ApiCall | 13963-14108 |
| `POST /manage/v2/databases/{id&#124;name}/partitions` | Raw HTTP / custom ApiCall | 14109-14287 |
| `DELETE /manage/v2/databases/{id&#124;name}/partitions/{name}` | Raw HTTP / custom ApiCall | 14288-14332 |
| `GET /manage/v2/databases/{id&#124;name}/partitions/{name}` | Raw HTTP / custom ApiCall | 14333-14505 |
| `PUT /manage/v2/databases/{id&#124;name}/partitions/{name}` | Raw HTTP / custom ApiCall | 14506-14714 |
| `GET /manage/v2/databases/{id&#124;name}/partitions/{name}/properties` | Raw HTTP / custom ApiCall | 14715-14768 |
| `PUT /manage/v2/databases/{id&#124;name}/partitions/{name}/properties` | Raw HTTP / custom ApiCall | 14769-14851 |
| `GET /manage/v2/databases/{id&#124;name}/pipelines` | Raw HTTP / custom ApiCall | 14852-14955 |
| `POST /manage/v2/databases/{id&#124;name}/pipelines` | Raw HTTP / custom ApiCall | 14956-15139 |
| `DELETE /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}` | Raw HTTP / custom ApiCall | 15140-15176 |
| `GET /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}` | Raw HTTP / custom ApiCall | 15177-15305 |
| `GET /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 15306-15435 |
| `PUT /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 15436-15562 |
| `GET /manage/v2/databases/{id&#124;name}/properties` | `ml.manage.databases.get_properties` (sync and async) | 15563-16486 |
| `PUT /manage/v2/databases/{id&#124;name}/properties` | `ml.manage.databases.put_properties` (sync and async) | 16487-17465 |
| `GET /manage/v2/databases/{id&#124;name}/rebalancer` | Raw HTTP / custom ApiCall | 17466-17552 |
| `PUT /manage/v2/databases/{id&#124;name}/rebalancer` | Raw HTTP / custom ApiCall | 17553-17622 |
| `GET /manage/v2/databases/{id&#124;name}/temporal` | Raw HTTP / custom ApiCall | 17623-17740 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/axes` | Raw HTTP / custom ApiCall | 17741-17833 |
| `POST /manage/v2/databases/{id&#124;name}/temporal/axes` | Raw HTTP / custom ApiCall | 17834-17918 |
| `DELETE /manage/v2/databases/{id&#124;name}/temporal/axes/{id&#124;name}` | Raw HTTP / custom ApiCall | 17919-17959 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/axes/{id&#124;name}` | Raw HTTP / custom ApiCall | 17960-18084 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/axes/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 18085-18142 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections` | Raw HTTP / custom ApiCall | 18143-18241 |
| `POST /manage/v2/databases/{id&#124;name}/temporal/collections` | Raw HTTP / custom ApiCall | 18242-18319 |
| `DELETE /manage/v2/databases/{id&#124;name}/temporal/collections?collection={name}` | Raw HTTP / custom ApiCall | 18320-18363 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections?collection={name}` | Raw HTTP / custom ApiCall | 18364-18489 |
| `POST /manage/v2/databases/{id&#124;name}/temporal/collections?collection={name}` | Raw HTTP / custom ApiCall | 18490-18576 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections/lsqt/properties?collection={name}` | Raw HTTP / custom ApiCall | 18577-18631 |
| `PUT /manage/v2/databases/{id&#124;name}/temporal/collections/lsqt/properties?collection={name}` | Raw HTTP / custom ApiCall | 18632-18695 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections/properties?collection={name}` | Raw HTTP / custom ApiCall | 18696-18757 |
| `PUT /manage/v2/databases/{id&#124;name}/temporal/collections/properties?collection={name}` | Raw HTTP / custom ApiCall | 18758-18816 |
| `GET /manage/v2/databases/{id&#124;name}/triggers` | Raw HTTP / custom ApiCall | 18817-18916 |
| `POST /manage/v2/databases/{id&#124;name}/triggers` | Raw HTTP / custom ApiCall | 18917-19063 |
| `DELETE /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}` | Raw HTTP / custom ApiCall | 19064-19104 |
| `GET /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}` | Raw HTTP / custom ApiCall | 19105-19227 |
| `GET /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 19228-19349 |
| `PUT /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 19350-19476 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas` | Raw HTTP / custom ApiCall | 19477-19577 |
| `POST /manage/v2/databases/{id&#124;name}/view-schemas` | Raw HTTP / custom ApiCall | 19578-19644 |
| `DELETE /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}` | Raw HTTP / custom ApiCall | 19645-19683 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}` | Raw HTTP / custom ApiCall | 19684-19809 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 19810-19872 |
| `PUT /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 19873-19940 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views` | Raw HTTP / custom ApiCall | 19941-20041 |
| `POST /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views` | Raw HTTP / custom ApiCall | 20042-20207 |
| `DELETE /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}` | Raw HTTP / custom ApiCall | 20208-20246 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}` | Raw HTTP / custom ApiCall | 20247-20372 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 20373-20459 |
| `PUT /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 20460-20549 |
| `GET /manage/v2/external-security` | Raw HTTP / custom ApiCall | 20550-20653 |
| `POST /manage/v2/external-security` | Raw HTTP / custom ApiCall | 20654-20936 |
| `DELETE /manage/v2/external-security/{id&#124;name}` | Raw HTTP / custom ApiCall | 20937-20978 |
| `GET /manage/v2/external-security/{id&#124;name}` | Raw HTTP / custom ApiCall | 20979-21124 |
| `DELETE /manage/v2/external-security/{id&#124;name}/jwt-secrets` | Raw HTTP / custom ApiCall | 21125-21180 |
| `POST /manage/v2/external-security/{id&#124;name}/jwt-secrets` | Raw HTTP / custom ApiCall | 21181-21458 |
| `PUT /manage/v2/external-security/{id&#124;name}/jwt-secrets` | Raw HTTP / custom ApiCall | 21459-21736 |
| `GET /manage/v2/external-security/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 21737-21999 |
| `PUT /manage/v2/external-security/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 22000-22265 |
| `GET /manage/v2/forests` | `ml.manage.forests.get_list` (sync and async) | 22266-22413 |
| `POST /manage/v2/forests` | `ml.manage.forests.create` (sync and async) | 22414-22618 |
| `PUT /manage/v2/forests` | `ml.manage.forests.put` (sync and async) | 22619-22835 |
| `GET /manage/v2/forests?view=counts` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 22836-23433 |
| `GET /manage/v2/forests?view=metrics` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 23434-23488 |
| `GET /manage/v2/forests?view=status` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 23489-23925 |
| `GET /manage/v2/forests?view=storage` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 23926-24136 |
| `DELETE /manage/v2/forests/{id&#124;name}` | `ml.manage.forests.delete` (sync and async) | 24137-24180 |
| `GET /manage/v2/forests/{id&#124;name}` | `ml.manage.forests.get` (sync and async) | 24181-24324 |
| `POST /manage/v2/forests/{id&#124;name}` | `ml.manage.forests.post` (sync and async) | 24325-24475 |
| `GET /manage/v2/forests/{id&#124;name}?view=counts` | `ml.manage.forests.get` (sync and async); pass the documented query parameter (check wrapper validation) | 24476-25072 |
| `GET /manage/v2/forests/{id&#124;name}?view=status` | `ml.manage.forests.get` (sync and async); pass the documented query parameter (check wrapper validation) | 25073-25902 |
| `GET /manage/v2/forests/{id&#124;name}/properties` | `ml.manage.forests.get_properties` (sync and async) | 25903-26083 |
| `PUT /manage/v2/forests/{id&#124;name}/properties` | `ml.manage.forests.put_properties` (sync and async) | 26084-26262 |
| `GET /manage/v2/groups` | Raw HTTP / custom ApiCall | 26263-26398 |
| `POST /manage/v2/groups` | Raw HTTP / custom ApiCall | 26399-26635 |
| `DELETE /manage/v2/groups/{id&#124;name}` | Raw HTTP / custom ApiCall | 26636-26673 |
| `GET /manage/v2/groups/{id&#124;name}` | Raw HTTP / custom ApiCall | 26674-26817 |
| `POST /manage/v2/groups/{id&#124;name}` | Raw HTTP / custom ApiCall | 26818-26875 |
| `GET /manage/v2/groups/{id&#124;name}?view=counts` | Raw HTTP / custom ApiCall | 26876-26974 |
| `GET /manage/v2/groups/{id&#124;name}?view=status` | Raw HTTP / custom ApiCall | 26975-27545 |
| `GET /manage/v2/groups/{id&#124;name}/properties` | `ml.manage.groups.get_properties` (sync and async) | 27546-27787 |
| `PUT /manage/v2/groups/{id&#124;name}/properties` | `ml.manage.groups.put_properties` (sync and async) | 27788-28026 |
| `GET /manage/v2/hosts` | `ml.manage.hosts.get_list` (sync and async) | 28027-28170 |
| `POST /manage/v2/hosts` | Raw HTTP / custom ApiCall | 28171-28252 |
| `GET /manage/v2/hosts?view=metrics` | `ml.manage.hosts.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 28253-28307 |
| `GET /manage/v2/hosts?view=status` | `ml.manage.hosts.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 28308-28812 |
| `GET /manage/v2/hosts/{id&#124;name}` | Raw HTTP / custom ApiCall | 28813-28956 |
| `POST /manage/v2/hosts/{id&#124;name}` | Raw HTTP / custom ApiCall | 28957-29093 |
| `GET /manage/v2/hosts/{id&#124;name}?view=config` | Raw HTTP / custom ApiCall | 29094-29208 |
| `GET /manage/v2/hosts/{id&#124;name}?view=counts` | Raw HTTP / custom ApiCall | 29209-29307 |
| `GET /manage/v2/hosts/{id&#124;name}?view=status` | Raw HTTP / custom ApiCall | 29308-30768 |
| `GET /manage/v2/hosts/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 30769-30864 |
| `PUT /manage/v2/hosts/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 30865-30973 |
| `GET /manage/v2/logs` | `ml.manage.logs.get` (sync and async) | 30974-31022 |
| `GET /manage/v2/meters` | Raw HTTP / custom ApiCall | 31023-31081 |
| `GET /manage/v2/meters/labels` | Raw HTTP / custom ApiCall | 31082-31133 |
| `OPTIONS /manage/v2/meters/labels` | Raw HTTP / custom ApiCall | 31134-31174 |
| `POST /manage/v2/meters/labels` | Raw HTTP / custom ApiCall | 31175-31237 |
| `DELETE /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 31238-31260 |
| `GET /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 31261-31309 |
| `HEAD /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 31310-31333 |
| `OPTIONS /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 31334-31378 |
| `PUT /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 31379-31440 |
| `GET /manage/v2/meters/resources` | Raw HTTP / custom ApiCall | 31441-31559 |
| `GET /manage/v2/mimetypes` | Raw HTTP / custom ApiCall | 31560-31692 |
| `POST /manage/v2/mimetypes` | Raw HTTP / custom ApiCall | 31693-31843 |
| `DELETE /manage/v2/mimetypes/{id&#124;name}` | Raw HTTP / custom ApiCall | 31844-31882 |
| `GET /manage/v2/mimetypes/{id&#124;name}` | Raw HTTP / custom ApiCall | 31883-32007 |
| `GET /manage/v2/mimetypes/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 32008-32091 |
| `PUT /manage/v2/mimetypes/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 32092-32176 |
| `GET /manage/v2/privileges` | Raw HTTP / custom ApiCall | 32177-32279 |
| `POST /manage/v2/privileges` | Raw HTTP / custom ApiCall | 32280-32348 |
| `DELETE /manage/v2/privileges/{id&#124;name}` | Raw HTTP / custom ApiCall | 32349-32390 |
| `GET /manage/v2/privileges/{id&#124;name}` | Raw HTTP / custom ApiCall | 32391-32521 |
| `GET /manage/v2/privileges/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 32522-32583 |
| `PUT /manage/v2/privileges/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 32584-32652 |
| `GET /manage/v2/properties` | Raw HTTP / custom ApiCall | 32653-32753 |
| `PUT /manage/v2/properties` | Raw HTTP / custom ApiCall | 32754-32863 |
| `GET /manage/v2/protected-collections` | Raw HTTP / custom ApiCall | 32864-32966 |
| `POST /manage/v2/protected-collections` | Raw HTTP / custom ApiCall | 32967-33046 |
| `DELETE /manage/v2/protected-collections?collection={collection-uri}` | Raw HTTP / custom ApiCall | 33047-33089 |
| `GET /manage/v2/protected-collections?collection={collection-uri}` | Raw HTTP / custom ApiCall | 33090-33151 |
| `GET /manage/v2/protected-collections/properties?collection={collection-uri}` | Raw HTTP / custom ApiCall | 33152-33214 |
| `PUT /manage/v2/protected-collections/properties?collection={collection-uri}` | Raw HTTP / custom ApiCall | 33215-33283 |
| `GET /manage/v2/protected-paths` | Raw HTTP / custom ApiCall | 33284-33463 |
| `POST /manage/v2/protected-paths` | Raw HTTP / custom ApiCall | 33464-33578 |
| `GET /manage/v2/protected-paths/{id}/properties` | Raw HTTP / custom ApiCall | 33579-33697 |
| `PUT /manage/v2/protected-paths/{id}/properties` | Raw HTTP / custom ApiCall | 33698-33807 |
| `DELETE /manage/v2/protected-paths/{id&#124;name}` | Raw HTTP / custom ApiCall | 33808-33859 |
| `GET /manage/v2/protected-paths/{id&#124;name}` | Raw HTTP / custom ApiCall | 33860-34057 |
| `GET /manage/v2/query-rolesets` | Raw HTTP / custom ApiCall | 34058-34187 |
| `POST /manage/v2/query-rolesets` | Raw HTTP / custom ApiCall | 34188-34257 |
| `DELETE /manage/v2/query-rolesets/{id}` | Raw HTTP / custom ApiCall | 34258-34298 |
| `GET /manage/v2/query-rolesets/{id}` | Raw HTTP / custom ApiCall | 34299-34417 |
| `GET /manage/v2/query-rolesets/{id}/properties` | Raw HTTP / custom ApiCall | 34418-34511 |
| `GET /manage/v2/requests` | Raw HTTP / custom ApiCall | 34512-34779 |
| `GET /manage/v2/requests/{id&#124;uri}` | Raw HTTP / custom ApiCall | 34780-34961 |
| `GET /manage/v2/roles` | `ml.manage.roles.get_list` (sync and async) | 34962-35063 |
| `POST /manage/v2/roles` | `ml.manage.roles.create` (sync and async) | 35064-35239 |
| `DELETE /manage/v2/roles/{id&#124;name}` | `ml.manage.roles.delete` (sync and async) | 35240-35280 |
| `GET /manage/v2/roles/{id&#124;name}` | `ml.manage.roles.get` (sync and async) | 35281-35409 |
| `GET /manage/v2/roles/{id&#124;name}/properties` | `ml.manage.roles.get_properties` (sync and async) | 35410-35535 |
| `PUT /manage/v2/roles/{id&#124;name}/properties` | `ml.manage.roles.put_properties` (sync and async) | 35536-35711 |
| `GET /manage/v2/security` | Raw HTTP / custom ApiCall | 35712-35795 |
| `POST /manage/v2/security` | Raw HTTP / custom ApiCall | 35796-35847 |
| `GET /manage/v2/security/properties` | Raw HTTP / custom ApiCall | 35848-36026 |
| `PUT /manage/v2/security/properties` | Raw HTTP / custom ApiCall | 36027-36155 |
| `GET /manage/v2/servers` | `ml.manage.servers.get_list` (sync and async) | 36156-36338 |
| `POST /manage/v2/servers` | `ml.manage.servers.create` (sync and async) | 36339-37138 |
| `GET /manage/v2/servers?view=metrics` | `ml.manage.servers.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 37139-37194 |
| `GET /manage/v2/servers?view=status` | `ml.manage.servers.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 37195-37376 |
| `GET /manage/v2/servers?view=xdmp:server-status` | `ml.manage.servers.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 37377-37685 |
| `DELETE /manage/v2/servers/{id&#124;name}` | `ml.manage.servers.delete` (sync and async) | 37686-37727 |
| `GET /manage/v2/servers/{id&#124;name}` | `ml.manage.servers.get` (sync and async) | 37728-38943 |
| `GET /manage/v2/servers/{id&#124;name}?view=package` | `ml.manage.servers.get` (sync and async); pass the documented query parameter (check wrapper validation) | 38944-38991 |
| `GET /manage/v2/servers/{id&#124;name}?view=status` | `ml.manage.servers.get` (sync and async); pass the documented query parameter (check wrapper validation) | 38992-39401 |
| `GET /manage/v2/servers/{id&#124;name}/properties` | `ml.manage.servers.get_properties` (sync and async) | 39402-40170 |
| `PUT /manage/v2/servers/{id&#124;name}/properties` | `ml.manage.servers.put_properties` (sync and async) | 40171-40944 |
| `GET /manage/v2/support-request` | Raw HTTP / custom ApiCall | 40945-40988 |
| `GET /manage/v2/task-servers` | Raw HTTP / custom ApiCall | 40989-41031 |
| `GET /manage/v2/task-servers/{id&#124;name}` | Raw HTTP / custom ApiCall | 41032-41074 |
| `GET /manage/v2/task-servers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 41075-41215 |
| `PUT /manage/v2/task-servers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 41216-41356 |
| `GET /manage/v2/tasks` | Raw HTTP / custom ApiCall | 41357-41439 |
| `POST /manage/v2/tasks` | Raw HTTP / custom ApiCall | 41440-41550 |
| `DELETE /manage/v2/tasks/{id}` | Raw HTTP / custom ApiCall | 41551-41590 |
| `GET /manage/v2/tasks/{id}` | Raw HTTP / custom ApiCall | 41591-41693 |
| `GET /manage/v2/tasks/{id}/properties` | Raw HTTP / custom ApiCall | 41694-41799 |
| `PUT /manage/v2/tasks/{id}/properties` | Raw HTTP / custom ApiCall | 41800-41916 |
| `GET /manage/v2/tickets/{tid}?view=process-status` | Raw HTTP / custom ApiCall | 41917-42031 |
| `GET /manage/v2/transactions` | Raw HTTP / custom ApiCall | 42032-42263 |
| `GET /manage/v2/transactions/{id&#124;uri}` | Raw HTTP / custom ApiCall | 42264-42423 |
| `GET /manage/v2/usage-report` | Raw HTTP / custom ApiCall | 42424-42472 |
| `GET /manage/v2/users` | `ml.manage.users.get_list` (sync and async) | 42473-42574 |
| `POST /manage/v2/users` | `ml.manage.users.create` (sync and async) | 42575-42743 |
| `DELETE /manage/v2/users/{id&#124;name}` | `ml.manage.users.delete` (sync and async) | 42744-42784 |
| `GET /manage/v2/users/{id&#124;name}` | `ml.manage.users.get` (sync and async) | 42785-42911 |
| `GET /manage/v2/users/{id&#124;name}/properties` | `ml.manage.users.get_properties` (sync and async) | 42912-43026 |
| `PUT /manage/v2/users/{id&#124;name}/properties` | `ml.manage.users.put_properties` (sync and async) | 43027-43190 |
| `GET /manage/v3` | Raw HTTP / custom ApiCall | 43191-43337 |
| `POST /manage/v3` | Raw HTTP / custom ApiCall | 43338-43486 |
| `GET /v1/alert/match` | Raw HTTP / custom ApiCall | 43487-43625 |
| `POST /v1/alert/match` | Raw HTTP / custom ApiCall | 43626-43787 |
| `GET /v1/alert/rules` | Raw HTTP / custom ApiCall | 43788-43897 |
| `DELETE /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 43898-43938 |
| `GET /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 43939-44046 |
| `HEAD /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 44047-44100 |
| `PUT /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 44101-44203 |
| `GET /v1/config/indexes` | Raw HTTP / custom ApiCall | 44204-44304 |
| `GET /v1/config/indexes/{name}` | Raw HTTP / custom ApiCall | 44305-44398 |
| `DELETE /v1/config/namespaces` | Raw HTTP / custom ApiCall | 44399-44440 |
| `GET /v1/config/namespaces` | Raw HTTP / custom ApiCall | 44441-44552 |
| `POST /v1/config/namespaces` | Raw HTTP / custom ApiCall | 44553-44666 |
| `PUT /v1/config/namespaces` | Raw HTTP / custom ApiCall | 44667-44780 |
| `DELETE /v1/config/namespaces/{prefix}` | Raw HTTP / custom ApiCall | 44781-44823 |
| `GET /v1/config/namespaces/{prefix}` | Raw HTTP / custom ApiCall | 44824-44922 |
| `PUT /v1/config/namespaces/{prefix}` | Raw HTTP / custom ApiCall | 44923-45020 |
| `DELETE /v1/config/properties` | Raw HTTP / custom ApiCall | 45021-45053 |
| `GET /v1/config/properties` | Raw HTTP / custom ApiCall | 45054-45147 |
| `PUT /v1/config/properties` | Raw HTTP / custom ApiCall | 45148-45224 |
| `DELETE /v1/config/properties/{property-name}` | Raw HTTP / custom ApiCall | 45225-45255 |
| `GET /v1/config/properties/{property-name}` | Raw HTTP / custom ApiCall | 45256-45352 |
| `PUT /v1/config/properties/{property-name}` | Raw HTTP / custom ApiCall | 45353-45426 |
| `DELETE /v1/config/query` | Raw HTTP / custom ApiCall | 45427-45465 |
| `GET /v1/config/query` | Raw HTTP / custom ApiCall | 45466-45583 |
| `DELETE /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 45584-45623 |
| `GET /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 45624-45757 |
| `POST /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 45758-45842 |
| `PUT /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 45843-45943 |
| `DELETE /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 45944-45973 |
| `GET /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 45974-46133 |
| `POST /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 46134-46256 |
| `PUT /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 46257-46386 |
| `GET /v1/config/resources` | Raw HTTP / custom ApiCall | 46387-46535 |
| `DELETE /v1/config/resources/{name}` | Raw HTTP / custom ApiCall | 46536-46575 |
| `GET /v1/config/resources/{name}` | Raw HTTP / custom ApiCall | 46576-46636 |
| `PUT /v1/config/resources/{name}` | Raw HTTP / custom ApiCall | 46637-46740 |
| `POST /v1/config/server` | Raw HTTP / custom ApiCall | 46741-46836 |
| `GET /v1/config/transforms` | Raw HTTP / custom ApiCall | 46837-46976 |
| `DELETE /v1/config/transforms/{name}` | Raw HTTP / custom ApiCall | 46977-47016 |
| `GET /v1/config/transforms/{name}` | Raw HTTP / custom ApiCall | 47017-47082 |
| `PUT /v1/config/transforms/{name}` | Raw HTTP / custom ApiCall | 47083-47181 |
| `DELETE /v1/documents` | `ml.rest.documents.delete` (sync and async) | 47182-47286 |
| `GET /v1/documents` | `ml.rest.documents.get` (sync and async) | 47287-47561 |
| `HEAD /v1/documents` | Raw HTTP / custom ApiCall | 47562-47621 |
| `PATCH /v1/documents` | Raw HTTP / custom ApiCall | 47622-47758 |
| `POST /v1/documents` | `ml.rest.documents.post` (sync and async) | 47759-47984 |
| `PUT /v1/documents` | Raw HTTP / custom ApiCall | 47985-48149 |
| `POST /v1/documents?extension={ext}` | `ml.rest.documents.post` (sync and async); pass the documented query parameter (check wrapper validation) | 48150-48292 |
| `POST /v1/documents?uri={db-uri}` | `ml.rest.documents.post` (sync and async); pass the documented query parameter (check wrapper validation) | 48293-48436 |
| `POST /v1/documents/protection` | Raw HTTP / custom ApiCall | 48437-48600 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/status` | Raw HTTP / custom ApiCall | 48601-48670 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets` | Raw HTTP / custom ApiCall | 48671-48741 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}` | Raw HTTP / custom ApiCall | 48742-48779 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 48780-48847 |
| `POST /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 48848-48895 |
| `DELETE /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules/ALERT_ID` | Raw HTTP / custom ApiCall | 48896-48937 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules/ALERT_ID` | Raw HTTP / custom ApiCall | 48938-48974 |
| `PUT /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules/ALERT_ID` | Raw HTTP / custom ApiCall | 48975-49012 |
| `POST /v1/eval` | `ml.rest.eval.post` (sync and async) | 49013-49170 |
| `DELETE /v1/ext/{directories}` | Raw HTTP / custom ApiCall | 49171-49214 |
| `GET /v1/ext/{directories}` | Raw HTTP / custom ApiCall | 49215-49329 |
| `DELETE /v1/ext/{directories}/{asset}` | Raw HTTP / custom ApiCall | 49330-49377 |
| `GET /v1/ext/{directories}/{asset}` | Raw HTTP / custom ApiCall | 49378-49446 |
| `PUT /v1/ext/{directories}/{asset}` | Raw HTTP / custom ApiCall | 49447-49521 |
| `DELETE /v1/graphs` | Raw HTTP / custom ApiCall | 49522-49632 |
| `GET /v1/graphs` | Raw HTTP / custom ApiCall | 49633-49809 |
| `HEAD /v1/graphs` | Raw HTTP / custom ApiCall | 49810-49864 |
| `POST /v1/graphs` | Raw HTTP / custom ApiCall | 49865-50029 |
| `PUT /v1/graphs` | Raw HTTP / custom ApiCall | 50030-50179 |
| `GET /v1/graphs/sparql` | Raw HTTP / custom ApiCall | 50180-50328 |
| `POST /v1/graphs/sparql` | Raw HTTP / custom ApiCall | 50329-50634 |
| `GET /v1/graphs/things` | Raw HTTP / custom ApiCall | 50635-50765 |
| `POST /v1/invoke` | Raw HTTP / custom ApiCall | 50766-50944 |
| `GET /v1/qbe` | Raw HTTP / custom ApiCall | 50945-51219 |
| `POST /v1/qbe` | Raw HTTP / custom ApiCall | 51220-51507 |
| `DELETE /v1/resources/{name}` | Raw HTTP / custom ApiCall | 51508-51560 |
| `GET /v1/resources/{name}` | Raw HTTP / custom ApiCall | 51561-51608 |
| `POST /v1/resources/{name}` | Raw HTTP / custom ApiCall | 51609-51662 |
| `PUT /v1/resources/{name}` | Raw HTTP / custom ApiCall | 51663-51715 |
| `GET /v1/rest-apis` | Raw HTTP / custom ApiCall | 51716-51814 |
| `POST /v1/rest-apis` | Raw HTTP / custom ApiCall | 51815-51918 |
| `DELETE /v1/rest-apis/{name}` | Raw HTTP / custom ApiCall | 51919-51998 |
| `GET /v1/rest-apis/{name}` | Raw HTTP / custom ApiCall | 51999-52108 |
| `GET /v1/rows` | Raw HTTP / custom ApiCall | 52109-52383 |
| `POST /v1/rows` | Raw HTTP / custom ApiCall | 52384-52681 |
| `GET /v1/rows/graphql` | Raw HTTP / custom ApiCall | 52682-52786 |
| `POST /v1/rows/graphql` | Raw HTTP / custom ApiCall | 52787-52889 |
| `POST /v1/rows/update` | Raw HTTP / custom ApiCall | 52890-53034 |
| `DELETE /v1/search` | Raw HTTP / custom ApiCall | 53035-53081 |
| `GET /v1/search` | Raw HTTP / custom ApiCall | 53082-53432 |
| `POST /v1/search` | Raw HTTP / custom ApiCall | 53433-53839 |
| `GET /v1/suggest` | Raw HTTP / custom ApiCall | 53840-53978 |
| `POST /v1/suggest` | Raw HTTP / custom ApiCall | 53979-54164 |
| `POST /v1/temporal/collections/{name}` | Raw HTTP / custom ApiCall | 54165-54224 |
| `POST /v1/transactions` | `ml.rest.transactions.create` (sync and async) | 54225-54300 |
| `GET /v1/transactions/{txid}` | `ml.rest.transactions.get` (sync and async) | 54301-54445 |
| `POST /v1/transactions/{txid}` | `ml.rest.transactions.post` (sync and async) | 54446-54504 |
| `GET /v1/values` | Raw HTTP / custom ApiCall | 54505-54649 |
| `GET /v1/values/{name}` | Raw HTTP / custom ApiCall | 54650-54832 |
| `POST /v1/values/{name}` | Raw HTTP / custom ApiCall | 54833-55206 |
