# MarkLogic 11: 401 endpoint contracts

Read only the relevant section of `v11.md`, using the inclusive line ranges below.
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
| `GET /manage/v2/clusters/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 5513-5592 |
| `PUT /manage/v2/clusters/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 5593-5680 |
| `DELETE /manage/v2/credentials/properties` | Raw HTTP / custom ApiCall | 5681-5722 |
| `GET /manage/v2/credentials/properties` | Raw HTTP / custom ApiCall | 5723-5788 |
| `PUT /manage/v2/credentials/properties` | Raw HTTP / custom ApiCall | 5789-5861 |
| `GET /manage/v2/credentials/secure` | Raw HTTP / custom ApiCall | 5862-5954 |
| `POST /manage/v2/credentials/secure` | Raw HTTP / custom ApiCall | 5955-6085 |
| `GET /manage/v2/databases` | `ml.manage.databases.get_list` (sync and async) | 6086-6219 |
| `POST /manage/v2/databases` | `ml.manage.databases.create` (sync and async) | 6220-7151 |
| `GET /manage/v2/databases?view=metrics` | `ml.manage.databases.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 7152-7205 |
| `DELETE /manage/v2/databases/{id&#124;name}` | `ml.manage.databases.delete` (sync and async) | 7206-7254 |
| `GET /manage/v2/databases/{id&#124;name}` | `ml.manage.databases.get` (sync and async) | 7255-7390 |
| `POST /manage/v2/databases/{id&#124;name}` | `ml.manage.databases.post` (sync and async) | 7391-7800 |
| `GET /manage/v2/databases/{id&#124;name}?view=counts` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 7801-7902 |
| `GET /manage/v2/databases/{id&#124;name}?view=describe-indexes` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 7903-7994 |
| `GET /manage/v2/databases/{id&#124;name}?view=package` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 7995-8041 |
| `GET /manage/v2/databases/{id&#124;name}?view=status` | `ml.manage.databases.get` (sync and async); pass the documented query parameter (check wrapper validation) | 8042-8579 |
| `GET /manage/v2/databases/{id&#124;name}/alert` | Raw HTTP / custom ApiCall | 8580-8698 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions` | Raw HTTP / custom ApiCall | 8699-8790 |
| `POST /manage/v2/databases/{id&#124;name}/alert/actions` | Raw HTTP / custom ApiCall | 8791-8869 |
| `DELETE /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}` | Raw HTTP / custom ApiCall | 8870-8912 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}` | Raw HTTP / custom ApiCall | 8913-9035 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 9036-9100 |
| `PUT /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 9101-9173 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 9174-9264 |
| `POST /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 9265-9444 |
| `DELETE /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}` | Raw HTTP / custom ApiCall | 9445-9487 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}` | Raw HTTP / custom ApiCall | 9488-9608 |
| `GET /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 9609-9677 |
| `PUT /manage/v2/databases/{id&#124;name}/alert/actions/{id&#124;name}/rules/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 9678-9843 |
| `DELETE /manage/v2/databases/{id&#124;name}/alert/configs` | Raw HTTP / custom ApiCall | 9844-9888 |
| `GET /manage/v2/databases/{id&#124;name}/alert/configs` | Raw HTTP / custom ApiCall | 9889-10019 |
| `POST /manage/v2/databases/{id&#124;name}/alert/configs` | Raw HTTP / custom ApiCall | 10020-10131 |
| `GET /manage/v2/databases/{id&#124;name}/alert/configs/properties` | Raw HTTP / custom ApiCall | 10132-10208 |
| `PUT /manage/v2/databases/{id&#124;name}/alert/configs/properties` | Raw HTTP / custom ApiCall | 10209-10296 |
| `GET /manage/v2/databases/{id&#124;name}/cpf-configs` | Raw HTTP / custom ApiCall | 10297-10398 |
| `POST /manage/v2/databases/{id&#124;name}/cpf-configs` | Raw HTTP / custom ApiCall | 10399-10511 |
| `DELETE /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}` | Raw HTTP / custom ApiCall | 10512-10548 |
| `GET /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}` | Raw HTTP / custom ApiCall | 10549-10673 |
| `GET /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}/properties` | Raw HTTP / custom ApiCall | 10674-10741 |
| `PUT /manage/v2/databases/{id&#124;name}/cpf-configs/{domain-id-or-default-domain-name}/properties` | Raw HTTP / custom ApiCall | 10742-10812 |
| `GET /manage/v2/databases/{id&#124;name}/domains` | Raw HTTP / custom ApiCall | 10813-10916 |
| `POST /manage/v2/databases/{id&#124;name}/domains` | Raw HTTP / custom ApiCall | 10917-11010 |
| `DELETE /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}` | Raw HTTP / custom ApiCall | 11011-11047 |
| `GET /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}` | Raw HTTP / custom ApiCall | 11048-11172 |
| `GET /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 11173-11250 |
| `PUT /manage/v2/databases/{id&#124;name}/domains/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 11251-11329 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep` | Raw HTTP / custom ApiCall | 11330-11451 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs` | Raw HTTP / custom ApiCall | 11452-11553 |
| `POST /manage/v2/databases/{id&#124;name}/flexrep/configs` | Raw HTTP / custom ApiCall | 11554-11610 |
| `DELETE /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}` | Raw HTTP / custom ApiCall | 11611-11648 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}` | Raw HTTP / custom ApiCall | 11649-11775 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 11776-11830 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 11831-11884 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets` | Raw HTTP / custom ApiCall | 11885-11987 |
| `POST /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets` | Raw HTTP / custom ApiCall | 11988-12138 |
| `DELETE /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}` | Raw HTTP / custom ApiCall | 12139-12177 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}` | Raw HTTP / custom ApiCall | 12178-12304 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 12305-12423 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/configs/{id&#124;name}/targets/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 12424-12545 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/properties` | Raw HTTP / custom ApiCall | 12546-12601 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/properties` | Raw HTTP / custom ApiCall | 12602-12657 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/pulls` | Raw HTTP / custom ApiCall | 12658-12760 |
| `POST /manage/v2/databases/{id&#124;name}/flexrep/pulls` | Raw HTTP / custom ApiCall | 12761-12878 |
| `DELETE /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}` | Raw HTTP / custom ApiCall | 12879-12915 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}` | Raw HTTP / custom ApiCall | 12916-13042 |
| `GET /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 13043-13139 |
| `PUT /manage/v2/databases/{id&#124;name}/flexrep/pulls/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 13140-13234 |
| `GET /manage/v2/databases/{id&#124;name}/partition-queries` | Raw HTTP / custom ApiCall | 13235-13380 |
| `POST /manage/v2/databases/{id&#124;name}/partition-queries` | Raw HTTP / custom ApiCall | 13381-13505 |
| `DELETE /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}` | Raw HTTP / custom ApiCall | 13506-13541 |
| `GET /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}` | Raw HTTP / custom ApiCall | 13542-13585 |
| `GET /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}/properties` | Raw HTTP / custom ApiCall | 13586-13639 |
| `PUT /manage/v2/databases/{id&#124;name}/partition-queries/{partition-number}/properties` | Raw HTTP / custom ApiCall | 13640-13738 |
| `GET /manage/v2/databases/{id&#124;name}/partitions` | Raw HTTP / custom ApiCall | 13739-13884 |
| `POST /manage/v2/databases/{id&#124;name}/partitions` | Raw HTTP / custom ApiCall | 13885-14063 |
| `DELETE /manage/v2/databases/{id&#124;name}/partitions/{name}` | Raw HTTP / custom ApiCall | 14064-14108 |
| `GET /manage/v2/databases/{id&#124;name}/partitions/{name}` | Raw HTTP / custom ApiCall | 14109-14281 |
| `PUT /manage/v2/databases/{id&#124;name}/partitions/{name}` | Raw HTTP / custom ApiCall | 14282-14490 |
| `GET /manage/v2/databases/{id&#124;name}/partitions/{name}/properties` | Raw HTTP / custom ApiCall | 14491-14544 |
| `PUT /manage/v2/databases/{id&#124;name}/partitions/{name}/properties` | Raw HTTP / custom ApiCall | 14545-14627 |
| `GET /manage/v2/databases/{id&#124;name}/pipelines` | Raw HTTP / custom ApiCall | 14628-14731 |
| `POST /manage/v2/databases/{id&#124;name}/pipelines` | Raw HTTP / custom ApiCall | 14732-14915 |
| `DELETE /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}` | Raw HTTP / custom ApiCall | 14916-14952 |
| `GET /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}` | Raw HTTP / custom ApiCall | 14953-15081 |
| `GET /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 15082-15211 |
| `PUT /manage/v2/databases/{id&#124;name}/pipelines/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 15212-15338 |
| `GET /manage/v2/databases/{id&#124;name}/properties` | `ml.manage.databases.get_properties` (sync and async) | 15339-16258 |
| `PUT /manage/v2/databases/{id&#124;name}/properties` | `ml.manage.databases.put_properties` (sync and async) | 16259-17233 |
| `GET /manage/v2/databases/{id&#124;name}/rebalancer` | Raw HTTP / custom ApiCall | 17234-17320 |
| `PUT /manage/v2/databases/{id&#124;name}/rebalancer` | Raw HTTP / custom ApiCall | 17321-17390 |
| `GET /manage/v2/databases/{id&#124;name}/temporal` | Raw HTTP / custom ApiCall | 17391-17508 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/axes` | Raw HTTP / custom ApiCall | 17509-17601 |
| `POST /manage/v2/databases/{id&#124;name}/temporal/axes` | Raw HTTP / custom ApiCall | 17602-17686 |
| `DELETE /manage/v2/databases/{id&#124;name}/temporal/axes/{id&#124;name}` | Raw HTTP / custom ApiCall | 17687-17727 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/axes/{id&#124;name}` | Raw HTTP / custom ApiCall | 17728-17852 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/axes/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 17853-17910 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections` | Raw HTTP / custom ApiCall | 17911-18009 |
| `POST /manage/v2/databases/{id&#124;name}/temporal/collections` | Raw HTTP / custom ApiCall | 18010-18087 |
| `DELETE /manage/v2/databases/{id&#124;name}/temporal/collections?collection={name}` | Raw HTTP / custom ApiCall | 18088-18131 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections?collection={name}` | Raw HTTP / custom ApiCall | 18132-18257 |
| `POST /manage/v2/databases/{id&#124;name}/temporal/collections?collection={name}` | Raw HTTP / custom ApiCall | 18258-18344 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections/lsqt/properties?collection={name}` | Raw HTTP / custom ApiCall | 18345-18399 |
| `PUT /manage/v2/databases/{id&#124;name}/temporal/collections/lsqt/properties?collection={name}` | Raw HTTP / custom ApiCall | 18400-18463 |
| `GET /manage/v2/databases/{id&#124;name}/temporal/collections/properties?collection={name}` | Raw HTTP / custom ApiCall | 18464-18525 |
| `PUT /manage/v2/databases/{id&#124;name}/temporal/collections/properties?collection={name}` | Raw HTTP / custom ApiCall | 18526-18584 |
| `GET /manage/v2/databases/{id&#124;name}/triggers` | Raw HTTP / custom ApiCall | 18585-18684 |
| `POST /manage/v2/databases/{id&#124;name}/triggers` | Raw HTTP / custom ApiCall | 18685-18831 |
| `DELETE /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}` | Raw HTTP / custom ApiCall | 18832-18872 |
| `GET /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}` | Raw HTTP / custom ApiCall | 18873-18995 |
| `GET /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 18996-19117 |
| `PUT /manage/v2/databases/{id&#124;name}/triggers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 19118-19244 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas` | Raw HTTP / custom ApiCall | 19245-19345 |
| `POST /manage/v2/databases/{id&#124;name}/view-schemas` | Raw HTTP / custom ApiCall | 19346-19412 |
| `DELETE /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}` | Raw HTTP / custom ApiCall | 19413-19451 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}` | Raw HTTP / custom ApiCall | 19452-19577 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 19578-19640 |
| `PUT /manage/v2/databases/{id&#124;name}/view-schemas/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 19641-19708 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views` | Raw HTTP / custom ApiCall | 19709-19809 |
| `POST /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views` | Raw HTTP / custom ApiCall | 19810-19975 |
| `DELETE /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}` | Raw HTTP / custom ApiCall | 19976-20014 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}` | Raw HTTP / custom ApiCall | 20015-20140 |
| `GET /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 20141-20227 |
| `PUT /manage/v2/databases/{id&#124;name}/view-schemas/{schema-name}/views/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 20228-20317 |
| `GET /manage/v2/external-security` | Raw HTTP / custom ApiCall | 20318-20421 |
| `POST /manage/v2/external-security` | Raw HTTP / custom ApiCall | 20422-20704 |
| `DELETE /manage/v2/external-security/{id&#124;name}` | Raw HTTP / custom ApiCall | 20705-20746 |
| `GET /manage/v2/external-security/{id&#124;name}` | Raw HTTP / custom ApiCall | 20747-20892 |
| `DELETE /manage/v2/external-security/{id&#124;name}/jwt-secrets` | Raw HTTP / custom ApiCall | 20893-20948 |
| `POST /manage/v2/external-security/{id&#124;name}/jwt-secrets` | Raw HTTP / custom ApiCall | 20949-21226 |
| `PUT /manage/v2/external-security/{id&#124;name}/jwt-secrets` | Raw HTTP / custom ApiCall | 21227-21504 |
| `GET /manage/v2/external-security/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 21505-21767 |
| `PUT /manage/v2/external-security/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 21768-22033 |
| `GET /manage/v2/forests` | `ml.manage.forests.get_list` (sync and async) | 22034-22181 |
| `POST /manage/v2/forests` | `ml.manage.forests.create` (sync and async) | 22182-22386 |
| `PUT /manage/v2/forests` | `ml.manage.forests.put` (sync and async) | 22387-22603 |
| `GET /manage/v2/forests?view=counts` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 22604-23201 |
| `GET /manage/v2/forests?view=metrics` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 23202-23256 |
| `GET /manage/v2/forests?view=status` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 23257-23693 |
| `GET /manage/v2/forests?view=storage` | `ml.manage.forests.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 23694-23904 |
| `DELETE /manage/v2/forests/{id&#124;name}` | `ml.manage.forests.delete` (sync and async) | 23905-23948 |
| `GET /manage/v2/forests/{id&#124;name}` | `ml.manage.forests.get` (sync and async) | 23949-24092 |
| `POST /manage/v2/forests/{id&#124;name}` | `ml.manage.forests.post` (sync and async) | 24093-24243 |
| `GET /manage/v2/forests/{id&#124;name}?view=counts` | `ml.manage.forests.get` (sync and async); pass the documented query parameter (check wrapper validation) | 24244-24840 |
| `GET /manage/v2/forests/{id&#124;name}?view=status` | `ml.manage.forests.get` (sync and async); pass the documented query parameter (check wrapper validation) | 24841-25658 |
| `GET /manage/v2/forests/{id&#124;name}/properties` | `ml.manage.forests.get_properties` (sync and async) | 25659-25839 |
| `PUT /manage/v2/forests/{id&#124;name}/properties` | `ml.manage.forests.put_properties` (sync and async) | 25840-26018 |
| `GET /manage/v2/groups` | Raw HTTP / custom ApiCall | 26019-26154 |
| `POST /manage/v2/groups` | Raw HTTP / custom ApiCall | 26155-26397 |
| `DELETE /manage/v2/groups/{id&#124;name}` | Raw HTTP / custom ApiCall | 26398-26435 |
| `GET /manage/v2/groups/{id&#124;name}` | Raw HTTP / custom ApiCall | 26436-26579 |
| `POST /manage/v2/groups/{id&#124;name}` | Raw HTTP / custom ApiCall | 26580-26637 |
| `GET /manage/v2/groups/{id&#124;name}?view=counts` | Raw HTTP / custom ApiCall | 26638-26736 |
| `GET /manage/v2/groups/{id&#124;name}?view=status` | Raw HTTP / custom ApiCall | 26737-27307 |
| `GET /manage/v2/groups/{id&#124;name}/properties` | `ml.manage.groups.get_properties` (sync and async) | 27308-27555 |
| `PUT /manage/v2/groups/{id&#124;name}/properties` | `ml.manage.groups.put_properties` (sync and async) | 27556-27800 |
| `GET /manage/v2/hosts` | `ml.manage.hosts.get_list` (sync and async) | 27801-27944 |
| `POST /manage/v2/hosts` | Raw HTTP / custom ApiCall | 27945-28026 |
| `GET /manage/v2/hosts?view=metrics` | `ml.manage.hosts.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 28027-28081 |
| `GET /manage/v2/hosts?view=status` | `ml.manage.hosts.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 28082-28586 |
| `GET /manage/v2/hosts/{id&#124;name}` | Raw HTTP / custom ApiCall | 28587-28730 |
| `POST /manage/v2/hosts/{id&#124;name}` | Raw HTTP / custom ApiCall | 28731-28867 |
| `GET /manage/v2/hosts/{id&#124;name}?view=config` | Raw HTTP / custom ApiCall | 28868-28982 |
| `GET /manage/v2/hosts/{id&#124;name}?view=counts` | Raw HTTP / custom ApiCall | 28983-29081 |
| `GET /manage/v2/hosts/{id&#124;name}?view=status` | Raw HTTP / custom ApiCall | 29082-30540 |
| `GET /manage/v2/hosts/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 30541-30636 |
| `PUT /manage/v2/hosts/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 30637-30745 |
| `GET /manage/v2/logs` | `ml.manage.logs.get` (sync and async) | 30746-30794 |
| `GET /manage/v2/meters` | Raw HTTP / custom ApiCall | 30795-30853 |
| `GET /manage/v2/meters/labels` | Raw HTTP / custom ApiCall | 30854-30905 |
| `OPTIONS /manage/v2/meters/labels` | Raw HTTP / custom ApiCall | 30906-30946 |
| `POST /manage/v2/meters/labels` | Raw HTTP / custom ApiCall | 30947-31009 |
| `DELETE /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 31010-31032 |
| `GET /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 31033-31081 |
| `HEAD /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 31082-31105 |
| `OPTIONS /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 31106-31150 |
| `PUT /manage/v2/meters/labels/{id&#124;name}` | Raw HTTP / custom ApiCall | 31151-31212 |
| `GET /manage/v2/meters/resources` | Raw HTTP / custom ApiCall | 31213-31331 |
| `GET /manage/v2/mimetypes` | Raw HTTP / custom ApiCall | 31332-31464 |
| `POST /manage/v2/mimetypes` | Raw HTTP / custom ApiCall | 31465-31615 |
| `DELETE /manage/v2/mimetypes/{id&#124;name}` | Raw HTTP / custom ApiCall | 31616-31654 |
| `GET /manage/v2/mimetypes/{id&#124;name}` | Raw HTTP / custom ApiCall | 31655-31779 |
| `GET /manage/v2/mimetypes/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 31780-31863 |
| `PUT /manage/v2/mimetypes/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 31864-31948 |
| `GET /manage/v2/privileges` | Raw HTTP / custom ApiCall | 31949-32051 |
| `POST /manage/v2/privileges` | Raw HTTP / custom ApiCall | 32052-32120 |
| `DELETE /manage/v2/privileges/{id&#124;name}` | Raw HTTP / custom ApiCall | 32121-32162 |
| `GET /manage/v2/privileges/{id&#124;name}` | Raw HTTP / custom ApiCall | 32163-32293 |
| `GET /manage/v2/privileges/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 32294-32355 |
| `PUT /manage/v2/privileges/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 32356-32424 |
| `GET /manage/v2/properties` | Raw HTTP / custom ApiCall | 32425-32515 |
| `PUT /manage/v2/properties` | Raw HTTP / custom ApiCall | 32516-32615 |
| `GET /manage/v2/protected-collections` | Raw HTTP / custom ApiCall | 32616-32718 |
| `POST /manage/v2/protected-collections` | Raw HTTP / custom ApiCall | 32719-32798 |
| `DELETE /manage/v2/protected-collections?collection={collection-uri}` | Raw HTTP / custom ApiCall | 32799-32841 |
| `GET /manage/v2/protected-collections?collection={collection-uri}` | Raw HTTP / custom ApiCall | 32842-32903 |
| `GET /manage/v2/protected-collections/properties?collection={collection-uri}` | Raw HTTP / custom ApiCall | 32904-32966 |
| `PUT /manage/v2/protected-collections/properties?collection={collection-uri}` | Raw HTTP / custom ApiCall | 32967-33035 |
| `GET /manage/v2/protected-paths` | Raw HTTP / custom ApiCall | 33036-33215 |
| `POST /manage/v2/protected-paths` | Raw HTTP / custom ApiCall | 33216-33330 |
| `GET /manage/v2/protected-paths/{id}/properties` | Raw HTTP / custom ApiCall | 33331-33449 |
| `PUT /manage/v2/protected-paths/{id}/properties` | Raw HTTP / custom ApiCall | 33450-33559 |
| `DELETE /manage/v2/protected-paths/{id&#124;name}` | Raw HTTP / custom ApiCall | 33560-33611 |
| `GET /manage/v2/protected-paths/{id&#124;name}` | Raw HTTP / custom ApiCall | 33612-33809 |
| `GET /manage/v2/query-rolesets` | Raw HTTP / custom ApiCall | 33810-33939 |
| `POST /manage/v2/query-rolesets` | Raw HTTP / custom ApiCall | 33940-34009 |
| `DELETE /manage/v2/query-rolesets/{id}` | Raw HTTP / custom ApiCall | 34010-34050 |
| `GET /manage/v2/query-rolesets/{id}` | Raw HTTP / custom ApiCall | 34051-34169 |
| `GET /manage/v2/query-rolesets/{id}/properties` | Raw HTTP / custom ApiCall | 34170-34263 |
| `GET /manage/v2/requests` | Raw HTTP / custom ApiCall | 34264-34531 |
| `GET /manage/v2/requests/{id&#124;uri}` | Raw HTTP / custom ApiCall | 34532-34713 |
| `GET /manage/v2/roles` | `ml.manage.roles.get_list` (sync and async) | 34714-34815 |
| `POST /manage/v2/roles` | `ml.manage.roles.create` (sync and async) | 34816-34991 |
| `DELETE /manage/v2/roles/{id&#124;name}` | `ml.manage.roles.delete` (sync and async) | 34992-35032 |
| `GET /manage/v2/roles/{id&#124;name}` | `ml.manage.roles.get` (sync and async) | 35033-35161 |
| `GET /manage/v2/roles/{id&#124;name}/properties` | `ml.manage.roles.get_properties` (sync and async) | 35162-35287 |
| `PUT /manage/v2/roles/{id&#124;name}/properties` | `ml.manage.roles.put_properties` (sync and async) | 35288-35463 |
| `GET /manage/v2/security` | Raw HTTP / custom ApiCall | 35464-35547 |
| `POST /manage/v2/security` | Raw HTTP / custom ApiCall | 35548-35599 |
| `GET /manage/v2/security/properties` | Raw HTTP / custom ApiCall | 35600-35778 |
| `PUT /manage/v2/security/properties` | Raw HTTP / custom ApiCall | 35779-35907 |
| `GET /manage/v2/servers` | `ml.manage.servers.get_list` (sync and async) | 35908-36090 |
| `POST /manage/v2/servers` | `ml.manage.servers.create` (sync and async) | 36091-36912 |
| `GET /manage/v2/servers?view=metrics` | `ml.manage.servers.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 36913-36968 |
| `GET /manage/v2/servers?view=status` | `ml.manage.servers.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 36969-37150 |
| `GET /manage/v2/servers?view=xdmp:server-status` | `ml.manage.servers.get_list` (sync and async); pass the documented query parameter (check wrapper validation) | 37151-37459 |
| `DELETE /manage/v2/servers/{id&#124;name}` | `ml.manage.servers.delete` (sync and async) | 37460-37501 |
| `GET /manage/v2/servers/{id&#124;name}` | `ml.manage.servers.get` (sync and async) | 37502-38739 |
| `GET /manage/v2/servers/{id&#124;name}?view=package` | `ml.manage.servers.get` (sync and async); pass the documented query parameter (check wrapper validation) | 38740-38787 |
| `GET /manage/v2/servers/{id&#124;name}?view=status` | `ml.manage.servers.get` (sync and async); pass the documented query parameter (check wrapper validation) | 38788-39197 |
| `GET /manage/v2/servers/{id&#124;name}/properties` | `ml.manage.servers.get_properties` (sync and async) | 39198-39988 |
| `PUT /manage/v2/servers/{id&#124;name}/properties` | `ml.manage.servers.put_properties` (sync and async) | 39989-40784 |
| `GET /manage/v2/support-request` | Raw HTTP / custom ApiCall | 40785-40828 |
| `GET /manage/v2/task-servers` | Raw HTTP / custom ApiCall | 40829-40871 |
| `GET /manage/v2/task-servers/{id&#124;name}` | Raw HTTP / custom ApiCall | 40872-40914 |
| `GET /manage/v2/task-servers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 40915-41055 |
| `PUT /manage/v2/task-servers/{id&#124;name}/properties` | Raw HTTP / custom ApiCall | 41056-41196 |
| `GET /manage/v2/tasks` | Raw HTTP / custom ApiCall | 41197-41279 |
| `POST /manage/v2/tasks` | Raw HTTP / custom ApiCall | 41280-41390 |
| `DELETE /manage/v2/tasks/{id}` | Raw HTTP / custom ApiCall | 41391-41430 |
| `GET /manage/v2/tasks/{id}` | Raw HTTP / custom ApiCall | 41431-41533 |
| `GET /manage/v2/tasks/{id}/properties` | Raw HTTP / custom ApiCall | 41534-41639 |
| `PUT /manage/v2/tasks/{id}/properties` | Raw HTTP / custom ApiCall | 41640-41756 |
| `GET /manage/v2/tickets/{tid}?view=process-status` | Raw HTTP / custom ApiCall | 41757-41871 |
| `GET /manage/v2/transactions` | Raw HTTP / custom ApiCall | 41872-42103 |
| `GET /manage/v2/transactions/{id&#124;uri}` | Raw HTTP / custom ApiCall | 42104-42263 |
| `GET /manage/v2/usage-report` | Raw HTTP / custom ApiCall | 42264-42312 |
| `GET /manage/v2/users` | `ml.manage.users.get_list` (sync and async) | 42313-42414 |
| `POST /manage/v2/users` | `ml.manage.users.create` (sync and async) | 42415-42583 |
| `DELETE /manage/v2/users/{id&#124;name}` | `ml.manage.users.delete` (sync and async) | 42584-42624 |
| `GET /manage/v2/users/{id&#124;name}` | `ml.manage.users.get` (sync and async) | 42625-42751 |
| `GET /manage/v2/users/{id&#124;name}/properties` | `ml.manage.users.get_properties` (sync and async) | 42752-42866 |
| `PUT /manage/v2/users/{id&#124;name}/properties` | `ml.manage.users.put_properties` (sync and async) | 42867-43030 |
| `GET /manage/v3` | Raw HTTP / custom ApiCall | 43031-43177 |
| `POST /manage/v3` | Raw HTTP / custom ApiCall | 43178-43326 |
| `GET /v1/alert/match` | Raw HTTP / custom ApiCall | 43327-43465 |
| `POST /v1/alert/match` | Raw HTTP / custom ApiCall | 43466-43627 |
| `GET /v1/alert/rules` | Raw HTTP / custom ApiCall | 43628-43737 |
| `DELETE /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 43738-43778 |
| `GET /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 43779-43886 |
| `HEAD /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 43887-43940 |
| `PUT /v1/alert/rules/{name}` | Raw HTTP / custom ApiCall | 43941-44043 |
| `GET /v1/config/indexes` | Raw HTTP / custom ApiCall | 44044-44144 |
| `GET /v1/config/indexes/{name}` | Raw HTTP / custom ApiCall | 44145-44238 |
| `DELETE /v1/config/namespaces` | Raw HTTP / custom ApiCall | 44239-44280 |
| `GET /v1/config/namespaces` | Raw HTTP / custom ApiCall | 44281-44392 |
| `POST /v1/config/namespaces` | Raw HTTP / custom ApiCall | 44393-44506 |
| `PUT /v1/config/namespaces` | Raw HTTP / custom ApiCall | 44507-44620 |
| `DELETE /v1/config/namespaces/{prefix}` | Raw HTTP / custom ApiCall | 44621-44663 |
| `GET /v1/config/namespaces/{prefix}` | Raw HTTP / custom ApiCall | 44664-44762 |
| `PUT /v1/config/namespaces/{prefix}` | Raw HTTP / custom ApiCall | 44763-44860 |
| `DELETE /v1/config/properties` | Raw HTTP / custom ApiCall | 44861-44893 |
| `GET /v1/config/properties` | Raw HTTP / custom ApiCall | 44894-44987 |
| `PUT /v1/config/properties` | Raw HTTP / custom ApiCall | 44988-45064 |
| `DELETE /v1/config/properties/{property-name}` | Raw HTTP / custom ApiCall | 45065-45095 |
| `GET /v1/config/properties/{property-name}` | Raw HTTP / custom ApiCall | 45096-45192 |
| `PUT /v1/config/properties/{property-name}` | Raw HTTP / custom ApiCall | 45193-45266 |
| `DELETE /v1/config/query` | Raw HTTP / custom ApiCall | 45267-45305 |
| `GET /v1/config/query` | Raw HTTP / custom ApiCall | 45306-45423 |
| `DELETE /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 45424-45463 |
| `GET /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 45464-45597 |
| `POST /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 45598-45682 |
| `PUT /v1/config/query/(default&#124;{name})` | Raw HTTP / custom ApiCall | 45683-45783 |
| `DELETE /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 45784-45813 |
| `GET /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 45814-45973 |
| `POST /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 45974-46096 |
| `PUT /v1/config/query/(default&#124;{name})/{child-element}` | Raw HTTP / custom ApiCall | 46097-46226 |
| `GET /v1/config/resources` | Raw HTTP / custom ApiCall | 46227-46375 |
| `DELETE /v1/config/resources/{name}` | Raw HTTP / custom ApiCall | 46376-46415 |
| `GET /v1/config/resources/{name}` | Raw HTTP / custom ApiCall | 46416-46476 |
| `PUT /v1/config/resources/{name}` | Raw HTTP / custom ApiCall | 46477-46580 |
| `POST /v1/config/server` | Raw HTTP / custom ApiCall | 46581-46676 |
| `GET /v1/config/transforms` | Raw HTTP / custom ApiCall | 46677-46816 |
| `DELETE /v1/config/transforms/{name}` | Raw HTTP / custom ApiCall | 46817-46856 |
| `GET /v1/config/transforms/{name}` | Raw HTTP / custom ApiCall | 46857-46922 |
| `PUT /v1/config/transforms/{name}` | Raw HTTP / custom ApiCall | 46923-47021 |
| `DELETE /v1/documents` | `ml.rest.documents.delete` (sync and async) | 47022-47126 |
| `GET /v1/documents` | `ml.rest.documents.get` (sync and async) | 47127-47401 |
| `HEAD /v1/documents` | Raw HTTP / custom ApiCall | 47402-47461 |
| `PATCH /v1/documents` | Raw HTTP / custom ApiCall | 47462-47598 |
| `POST /v1/documents` | `ml.rest.documents.post` (sync and async) | 47599-47824 |
| `PUT /v1/documents` | Raw HTTP / custom ApiCall | 47825-47989 |
| `POST /v1/documents?extension={ext}` | `ml.rest.documents.post` (sync and async); pass the documented query parameter (check wrapper validation) | 47990-48132 |
| `POST /v1/documents?uri={db-uri}` | `ml.rest.documents.post` (sync and async); pass the documented query parameter (check wrapper validation) | 48133-48276 |
| `POST /v1/documents/protection` | Raw HTTP / custom ApiCall | 48277-48440 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/status` | Raw HTTP / custom ApiCall | 48441-48510 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets` | Raw HTTP / custom ApiCall | 48511-48581 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}` | Raw HTTP / custom ApiCall | 48582-48619 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 48620-48687 |
| `POST /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules` | Raw HTTP / custom ApiCall | 48688-48735 |
| `DELETE /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules/ALERT_ID` | Raw HTTP / custom ApiCall | 48736-48777 |
| `GET /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules/ALERT_ID` | Raw HTTP / custom ApiCall | 48778-48814 |
| `PUT /v1/domains/{domain-id-or-default-domain-name}/targets/{id&#124;name}/rules/ALERT_ID` | Raw HTTP / custom ApiCall | 48815-48852 |
| `POST /v1/eval` | `ml.rest.eval.post` (sync and async) | 48853-49010 |
| `DELETE /v1/ext/{directories}` | Raw HTTP / custom ApiCall | 49011-49054 |
| `GET /v1/ext/{directories}` | Raw HTTP / custom ApiCall | 49055-49169 |
| `DELETE /v1/ext/{directories}/{asset}` | Raw HTTP / custom ApiCall | 49170-49217 |
| `GET /v1/ext/{directories}/{asset}` | Raw HTTP / custom ApiCall | 49218-49286 |
| `PUT /v1/ext/{directories}/{asset}` | Raw HTTP / custom ApiCall | 49287-49361 |
| `DELETE /v1/graphs` | Raw HTTP / custom ApiCall | 49362-49472 |
| `GET /v1/graphs` | Raw HTTP / custom ApiCall | 49473-49649 |
| `HEAD /v1/graphs` | Raw HTTP / custom ApiCall | 49650-49704 |
| `POST /v1/graphs` | Raw HTTP / custom ApiCall | 49705-49869 |
| `PUT /v1/graphs` | Raw HTTP / custom ApiCall | 49870-50019 |
| `GET /v1/graphs/sparql` | Raw HTTP / custom ApiCall | 50020-50168 |
| `POST /v1/graphs/sparql` | Raw HTTP / custom ApiCall | 50169-50474 |
| `GET /v1/graphs/things` | Raw HTTP / custom ApiCall | 50475-50605 |
| `POST /v1/invoke` | Raw HTTP / custom ApiCall | 50606-50784 |
| `GET /v1/qbe` | Raw HTTP / custom ApiCall | 50785-51059 |
| `POST /v1/qbe` | Raw HTTP / custom ApiCall | 51060-51347 |
| `DELETE /v1/resources/{name}` | Raw HTTP / custom ApiCall | 51348-51400 |
| `GET /v1/resources/{name}` | Raw HTTP / custom ApiCall | 51401-51448 |
| `POST /v1/resources/{name}` | Raw HTTP / custom ApiCall | 51449-51502 |
| `PUT /v1/resources/{name}` | Raw HTTP / custom ApiCall | 51503-51555 |
| `GET /v1/rest-apis` | Raw HTTP / custom ApiCall | 51556-51654 |
| `POST /v1/rest-apis` | Raw HTTP / custom ApiCall | 51655-51758 |
| `DELETE /v1/rest-apis/{name}` | Raw HTTP / custom ApiCall | 51759-51838 |
| `GET /v1/rest-apis/{name}` | Raw HTTP / custom ApiCall | 51839-51948 |
| `GET /v1/rows` | Raw HTTP / custom ApiCall | 51949-52223 |
| `POST /v1/rows` | Raw HTTP / custom ApiCall | 52224-52521 |
| `GET /v1/rows/graphql` | Raw HTTP / custom ApiCall | 52522-52626 |
| `POST /v1/rows/graphql` | Raw HTTP / custom ApiCall | 52627-52729 |
| `POST /v1/rows/update` | Raw HTTP / custom ApiCall | 52730-52874 |
| `DELETE /v1/search` | Raw HTTP / custom ApiCall | 52875-52921 |
| `GET /v1/search` | Raw HTTP / custom ApiCall | 52922-53272 |
| `POST /v1/search` | Raw HTTP / custom ApiCall | 53273-53679 |
| `GET /v1/suggest` | Raw HTTP / custom ApiCall | 53680-53818 |
| `POST /v1/suggest` | Raw HTTP / custom ApiCall | 53819-54004 |
| `POST /v1/temporal/collections/{name}` | Raw HTTP / custom ApiCall | 54005-54064 |
| `POST /v1/transactions` | `ml.rest.transactions.create` (sync and async) | 54065-54140 |
| `GET /v1/transactions/{txid}` | `ml.rest.transactions.get` (sync and async) | 54141-54285 |
| `POST /v1/transactions/{txid}` | `ml.rest.transactions.post` (sync and async) | 54286-54344 |
| `GET /v1/values` | Raw HTTP / custom ApiCall | 54345-54489 |
| `GET /v1/values/{name}` | Raw HTTP / custom ApiCall | 54490-54672 |
| `POST /v1/values/{name}` | Raw HTTP / custom ApiCall | 54673-55046 |
