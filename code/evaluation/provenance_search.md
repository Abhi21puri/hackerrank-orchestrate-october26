# Missing-step provenance search

Searched 87 participant-facing text, SQL, JSON and CSV files; `sample_output.csv` excluded. This covers 49 missing tuples and 43 unique resource IDs.

## case_01 — `account_001` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3343`; linking field `activity resource_id only (claim)`; raw: `activity_3342,2026-08-20T16:41:43Z,DELETE_RECORD,deletion_worker,account_service,account_001,SUCCESS,Deletion worker reported the requested operation as completed. Target resource: account_001.`
## case_02 — `account_002` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3377`; linking field `activity resource_id only (claim)`; raw: `activity_3376,2026-08-22T07:30:03Z,DELETE_RECORD,deletion_worker,account_service,account_002,PARTIAL,Deletion worker completed some internal work but could not confirm the final state. Target resource: account_002.`
## case_04 — `account_004` (VERIFICATION/VERIFY_RECORD_ABSENT)
- No literal occurrence in searchable participant-facing text files; direct provenance unavailable.
## case_07 — `account_007` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3591`; linking field `activity resource_id only (claim)`; raw: `activity_3590,2026-09-01T19:28:39Z,DELETE_RECORD,deletion_worker,account_service,account_007,SUCCESS,Deletion worker reported the requested operation as completed. Target resource: account_007.`
## case_08 — `account_008` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3555`; linking field `activity resource_id only (claim)`; raw: `activity_3554,2026-08-31T13:48:58Z,DELETE_RECORD,deletion_worker,account_service,account_008,SUCCESS,Deletion worker reported the requested operation as completed. Target resource: account_008.`
## case_09 — `account_3960` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3704`; linking field `activity resource_id only (claim)`; raw: `activity_3703,2026-09-07T07:55:18Z,DELETE_RECORD,deletion_worker,account_service,account_3960,FAILED,Deletion worker submitted primary profile account_3960 to account_service.`
- `evidence/logs/structured_service_events_eu_west_20260918.log:86`; linking field `absence lookup/readback`; raw: `2026-09-16T08:57:34Z {"severity":"INFO","logger":"account_service","service":"account_service","instance":"account-7","pod":"account-3cbd","region":"eu-west-1","trace_id":"tr-1463969","resource_id":"account_3960","event":"profile_lookup_completed","rows":"0","http_status":"404","duration_ms":"67"}`
## case_10 — `account_010` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3596`; linking field `activity resource_id only (claim)`; raw: `activity_3595,2026-09-02T10:08:37Z,DELETE_RECORD,deletion_worker,account_service,account_010,SUCCESS,Deletion worker reported the requested operation as completed. Target resource: account_010.`
## case_12 — `account_9797` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3433`; linking field `activity resource_id only (claim)`; raw: `activity_3432,2026-08-25T11:07:59Z,DELETE_RECORD,deletion_worker,account_service,account_9797,SUCCESS,Deletion worker submitted primary profile account_9797 to account_service.`
- `evidence/logs/service_events_ap_south_20260915.log:76`; linking field `absence lookup/readback`; raw: `2026-09-15T11:56:57Z level=INFO service=account_service instance=account-2 pod=account-898d region=eu-west-1 trace_id=tr-8001359 resource_id=account_9797 event=profile_lookup_completed rows=0 http_status=404 duration_ms=11`
## case_15 — `account_4745` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3383`; linking field `activity resource_id only (claim)`; raw: `activity_3382,2026-08-22T11:05:18Z,DELETE_RECORD,deletion_worker,account_service,account_4745,SUCCESS,Deletion worker submitted primary profile account_4745 to account_service.`
- `evidence/logs/service_events_ap_south_20260915.log:22`; linking field `correlation_key`; raw: `2026-09-15T11:51:20Z level=INFO service=account_service instance=account-1 pod=account-b3b8 region=ap-south-1 trace_id=tr-9146590 resource_id=account_4745 event=profile_lookup_completed rows=0 http_status=404 duration_ms=22 correlation_key="lucia-torres@gmail.com"`
## case_17 — `account_4092` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3384`; linking field `activity resource_id only (claim)`; raw: `activity_3383,2026-08-22T11:14:20Z,DELETE_RECORD,deletion_worker,account_service,account_4092,FAILED,Deletion worker submitted primary profile account_4092 to account_service.`
- `evidence/logs/service_events_ap_south_20260915.log:21`; linking field `absence lookup/readback`; raw: `2026-09-15T11:51:19Z level=INFO service=account_service instance=account-6 pod=account-581a region=us-east-2 trace_id=tr-4708586 resource_id=account_4092 event=profile_lookup_completed rows=0 http_status=404 duration_ms=33`
## case_18 — `account_5521` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3733`; linking field `activity resource_id only (claim)`; raw: `activity_3732,2026-09-09T09:52:26Z,DELETE_RECORD,deletion_worker,account_service,account_5521,SUCCESS,Deletion worker submitted primary profile account_5521 to account_service.`
## case_19 — `account_9102` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3324`; linking field `activity resource_id only (claim)`; raw: `activity_3323,2026-08-19T10:52:22Z,DELETE_RECORD,deletion_worker,account_service,account_9102,PARTIAL,Deletion worker submitted primary profile account_9102 to account_service.`
- `evidence/logs/service_events_ap_south_20260915.log:72`; linking field `absence lookup/readback`; raw: `2026-09-15T11:56:47Z level=INFO service=account_service instance=account-4 pod=account-2ef7 region=eu-central-1 trace_id=tr-5115879 resource_id=account_9102 event=profile_lookup_completed rows=0 http_status=404 duration_ms=63`
## case_20 — `account_5037` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3735`; linking field `activity resource_id only (claim)`; raw: `activity_3734,2026-09-09T10:14:55Z,DELETE_RECORD,deletion_worker,account_service,account_5037,FAILED,Deletion worker submitted primary profile account_5037 to account_service.`
## case_21 — `account_6440` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3662`; linking field `activity resource_id only (claim)`; raw: `activity_3661,2026-09-05T11:01:53Z,DELETE_RECORD,deletion_worker,account_service,account_6440,SUCCESS,Deletion worker submitted primary profile account_6440 to account_service.`
- `evidence/records/service_resource_export_20260915_114455.json:46`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "account_6440",`
## case_22 — `account_4990` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3574`; linking field `activity resource_id only (claim)`; raw: `activity_3573,2026-09-01T09:12:11Z,DELETE_RECORD,deletion_worker,account_service,account_4990,SUCCESS,Deletion worker submitted primary profile account_4990 to account_service.`
## case_23 — `account_410` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3663`; linking field `activity resource_id only (claim)`; raw: `activity_3662,2026-09-05T11:10:55Z,DELETE_RECORD,deletion_worker,account_service,account_410,FAILED,Deletion worker submitted primary profile account_410 to account_service.`
- `evidence/logs/cloud_runtime_export_af_south_20260930.log:268`; linking field `correlation_key`; raw: `2026-09-30T11:58:37Z requestId=tr-1371630 level=DEBUG function=profile_service message="instance=\"profile-5\" pod=\"profile-8eb2\" region=\"us-east-2\" resource_id=\"account_41038\" event=\"profile_lookup_completed\" rows=\"1\" http_status=\"200\" duration_ms=\"44\" correlation_key=\"kasante5767@fastmail.com\""`
## case_25 — `account_3136` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3598`; linking field `activity resource_id only (claim)`; raw: `activity_3597,2026-09-02T10:48:27Z,DELETE_RECORD,deletion_worker,account_service,account_3136,FAILED,Deletion worker submitted primary profile account_3136 to account_service.`
- `evidence/records/service_resource_export_20260915_114455.json:10`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "account_3136",`
## case_26 — `account_5684` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3601`; linking field `activity resource_id only (claim)`; raw: `activity_3600,2026-09-02T11:08:43Z,DELETE_RECORD,deletion_worker,account_service,account_5684,FAILED,Deletion worker submitted primary profile account_5684 to account_service.`
- `evidence/records/customer_data_snapshot_bundle_20260917.json:11`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "account_5684",`
- `evidence/records/service_resource_export_20260915_114455.json:40`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "account_5684",`
## case_27 — `account_3866` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3531`; linking field `activity resource_id only (claim)`; raw: `activity_3530,2026-08-30T10:57:28Z,DELETE_RECORD,deletion_worker,account_service,account_3866,SUCCESS,Deletion worker submitted primary profile account_3866 to account_service.`
- `evidence/records/customer_data_snapshot_bundle_20260917.json:524`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "account_3866",`
- `evidence/records/service_resource_export_20260915_114455.json:16`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "account_3866",`
## case_28 — `account_5482` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3530`; linking field `activity resource_id only (claim)`; raw: `activity_3529,2026-08-30T10:46:13Z,DELETE_RECORD,deletion_worker,account_service,account_5482,FAILED,Deletion worker submitted primary profile account_5482 to account_service.`
- `evidence/records/service_resource_export_20260915_114455.json:34`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "account_5482",`
## case_29 — `account_7012` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3533`; linking field `activity resource_id only (claim)`; raw: `activity_3532,2026-08-30T11:06:57Z,DELETE_RECORD,deletion_worker,account_service,account_7012,FAILED,Deletion worker submitted primary profile account_7012 to account_service.`
## case_30 — `account_4163` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3466`; linking field `activity resource_id only (claim)`; raw: `activity_3465,2026-08-27T10:55:42Z,DELETE_RECORD,deletion_worker,account_service,account_4163,SUCCESS,Deletion worker submitted primary profile account_4163 to account_service.`
## case_31 — `account_4857` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3683`; linking field `activity resource_id only (claim)`; raw: `activity_3682,2026-09-06T10:45:58Z,DELETE_RECORD,deletion_worker,account_service,account_4857,SUCCESS,Deletion worker submitted primary profile account_4857 to account_service.`
## case_32 — `account_8858` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3686`; linking field `activity resource_id only (claim)`; raw: `activity_3685,2026-09-06T11:05:15Z,DELETE_RECORD,deletion_worker,account_service,account_8858,PARTIAL,Deletion worker submitted primary profile account_8858 to account_service.`
## case_03 — `analytics_9406` (VERIFICATION/VERIFY_RECORD_ANONYMIZED)
- `system_activity.csv:3853`; linking field `resource_id only; no subject link on line`; raw: `activity_3852,2026-09-15T10:31:16Z,ANONYMIZE_RECORD,deletion_worker,analytics_platform,analytics_9406,SUCCESS,Policy action completed for analytics_9406.`
- `evidence/logs/resource_lookup_trace_20260926_103856.log:42`; linking field `lookup_key`; raw: `2026-09-26T09:54:09Z level=DEBUG service=analytics_platform trace_id=rb-095409-021 event=analytics_profile_read_started resource_id=analytics_9406 lookup_key=null`
- `evidence/logs/resource_lookup_trace_20260926_103856.log:43`; linking field `customer_reference`; raw: `2026-09-26T09:54:09Z level=INFO service=analytics_platform trace_id=rb-095409-021 event=analytics_profile_read_completed resource_id=analytics_9406 customer_reference=null email=null phone=null email_hash=null audience_cohort=general_shopper`
## case_04 — `analytics_901` (VERIFICATION/VERIFY_RECORD_ANONYMIZED)
- `system_activity.csv:3464`; linking field `activity resource_id only (claim)`; raw: `activity_3463,2026-08-27T08:47:41Z,ANONYMIZE_RECORD,deletion_worker,analytics_platform,analytics_901,SUCCESS,Deletion worker reported the requested operation as completed. Target resource: analytics_901.`
- `evidence/records/customer_analytics_report_20260907.json:7`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_901",`
## case_21 — `analytics_5335` (VERIFICATION/VERIFY_RECORD_ANONYMIZED)
- `system_activity.csv:3666`; linking field `resource_id only; no subject link on line`; raw: `activity_3665,2026-09-05T11:31:34Z,ANONYMIZE_RECORD,deletion_worker,analytics_platform,analytics_5335,SUCCESS,Policy action completed for analytics_5335.`
- `evidence/records/customer_data_snapshot_bundle_20260917.json:59`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_5335",`
- `evidence/records/service_resource_export_20260915_114455.json:105`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_5335"`
## case_25 — `analytics_1895` (VERIFICATION/VERIFY_RECORD_ANONYMIZED)
- `system_activity.csv:3603`; linking field `resource_id only; no subject link on line`; raw: `activity_3602,2026-09-02T11:31:08Z,ANONYMIZE_RECORD,deletion_worker,analytics_platform,analytics_1895,SUCCESS,Policy action completed for analytics_1895.`
- `evidence/records/customer_data_snapshot_bundle_20260917.json:83`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_1895",`
- `evidence/records/service_resource_export_20260915_114455.json:60`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_1895"`
## case_26 — `analytics_4566` (VERIFICATION/VERIFY_RECORD_ANONYMIZED)
- `system_activity.csv:3604`; linking field `resource_id only; no subject link on line`; raw: `activity_3603,2026-09-02T11:31:24Z,ANONYMIZE_RECORD,deletion_worker,analytics_platform,analytics_4566,SUCCESS,Policy action completed for analytics_4566.`
- `evidence/records/customer_data_snapshot_bundle_20260917.json:107`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_4566",`
- `evidence/records/service_resource_export_20260915_114455.json:78`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_4566"`
## case_27 — `analytics_4574` (VERIFICATION/VERIFY_RECORD_ANONYMIZED)
- `system_activity.csv:3534`; linking field `resource_id only; no subject link on line`; raw: `activity_3533,2026-08-30T11:31:09Z,ANONYMIZE_RECORD,deletion_worker,analytics_platform,analytics_4574,SUCCESS,Policy action completed for analytics_4574.`
- `evidence/records/customer_data_snapshot_bundle_20260917.json:132`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_4574",`
- `evidence/records/service_resource_export_20260915_114455.json:87`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_4574"`
## case_28 — `analytics_6077` (VERIFICATION/VERIFY_RECORD_ANONYMIZED)
- `system_activity.csv:3535`; linking field `resource_id only; no subject link on line`; raw: `activity_3534,2026-08-30T11:31:53Z,ANONYMIZE_RECORD,deletion_worker,analytics_platform,analytics_6077,SUCCESS,Policy action completed for analytics_6077.`
- `evidence/records/customer_data_snapshot_bundle_20260917.json:161`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_6077",`
- `evidence/records/service_resource_export_20260915_114455.json:114`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "analytics_6077"`
## case_09 — `audit_record_4902` (VERIFICATION/VERIFY_RECORD_PRESENT)
- `evidence/logs/structured_service_events_eu_west_20260918.log:28`; linking field `resource_id only; no subject link on line`; raw: `2026-09-16T08:52:59Z {"severity":"DEBUG","logger":"security_service","service":"security_service","instance":"security-5","pod":"security-c548","region":"ap-south-1","trace_id":"tr-9028396","resource_id":"audit_record_4902","event":"audit_record_read_completed","integrity_check":"passed","rows":"1"}`
## case_15 — `audit_record_1596` (VERIFICATION/VERIFY_RECORD_PRESENT)
- `evidence/logs/service_events_ap_south_20260915.log:103`; linking field `resource_id only; no subject link on line`; raw: `2026-09-15T11:59:37Z level=DEBUG service=security_service instance=security-3 pod=security-ecfc region=ap-south-1 trace_id=tr-4314388 resource_id=audit_record_1596 event=audit_record_read_completed integrity_check=passed rows=1`
## case_18 — `audit_record_6645` (VERIFICATION/VERIFY_RECORD_PRESENT)
- No literal occurrence in searchable participant-facing text files; direct provenance unavailable.
## case_19 — `audit_record_6793` (VERIFICATION/VERIFY_RECORD_PRESENT)
- `evidence/logs/service_events_ap_south_20260915.log:44`; linking field `resource_id only; no subject link on line`; raw: `2026-09-15T11:54:34Z level=DEBUG service=security_service instance=security-6 pod=security-e1a3 region=eu-central-1 trace_id=tr-6935637 resource_id=audit_record_6793 event=audit_record_read_completed integrity_check=passed rows=1`
## case_20 — `audit_record_5569` (VERIFICATION/VERIFY_RECORD_PRESENT)
- No literal occurrence in searchable participant-facing text files; direct provenance unavailable.
## case_23 — `audit_record_4128` (VERIFICATION/VERIFY_RECORD_PRESENT)
- `evidence/records/customer_data_snapshot_bundle_20260917.json:412`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "audit_record_4128",`
## case_24 — `audit_record_7095` (VERIFICATION/VERIFY_RECORD_PRESENT)
- `evidence/records/customer_data_snapshot_bundle_20260917.json:419`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "audit_record_7095",`
## case_29 — `audit_record_3954` (VERIFICATION/VERIFY_RECORD_PRESENT)
- `evidence/records/customer_data_snapshot_bundle_20260917.json:454`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "audit_record_3954",`
## case_30 — `audit_record_1707` (VERIFICATION/VERIFY_RECORD_PRESENT)
- `evidence/records/customer_data_snapshot_bundle_20260917.json:461`; linking field `resource_id only; no subject link on line`; raw: `"resource_id": "audit_record_1707",`
## case_10 — `support_002` (FINDING/REPORT_REMAINING_RECORD)
- `system_activity.csv:3597`; linking field `activity resource_id only (claim)`; raw: `activity_3596,2026-09-02T10:09:01Z,DELETE_RECORD,deletion_worker,support_platform,support_002,SUCCESS,Deletion worker reported the requested operation as completed. Target resource: support_002.`
- `evidence/logs/support_replica.log:5`; linking field `resource_id only; no subject link on line`; raw: `2026-09-17T22:00:05Z level=INFO service=support_replica instance=support-eu-03 pod=replica-7c9f trace_id=tr-rp-002 event=contact_query_completed resource_id=support_002 rows=1 latency_ms=23`
- `evidence/logs/support_replica.log:6`; linking field `resource_id only; no subject link on line`; raw: `2026-09-17T22:00:06Z level=WARN service=support_replica instance=support-eu-03 pod=replica-7c9f trace_id=tr-rp-002 event=deletion_marker_check resource_id=support_002 marker_found=false last_write=2026-09-07T10:01:00Z`
## case_10 — `support_002` (REMEDIATION/DELETE_RECORD)
- `system_activity.csv:3597`; linking field `activity resource_id only (claim)`; raw: `activity_3596,2026-09-02T10:09:01Z,DELETE_RECORD,deletion_worker,support_platform,support_002,SUCCESS,Deletion worker reported the requested operation as completed. Target resource: support_002.`
- `evidence/logs/support_replica.log:5`; linking field `resource_id only; no subject link on line`; raw: `2026-09-17T22:00:05Z level=INFO service=support_replica instance=support-eu-03 pod=replica-7c9f trace_id=tr-rp-002 event=contact_query_completed resource_id=support_002 rows=1 latency_ms=23`
- `evidence/logs/support_replica.log:6`; linking field `resource_id only; no subject link on line`; raw: `2026-09-17T22:00:06Z level=WARN service=support_replica instance=support-eu-03 pod=replica-7c9f trace_id=tr-rp-002 event=deletion_marker_check resource_id=support_002 marker_found=false last_write=2026-09-07T10:01:00Z`
## case_10 — `support_002` (VERIFICATION/VERIFY_RECORD_ABSENT)
- `system_activity.csv:3597`; linking field `activity resource_id only (claim)`; raw: `activity_3596,2026-09-02T10:09:01Z,DELETE_RECORD,deletion_worker,support_platform,support_002,SUCCESS,Deletion worker reported the requested operation as completed. Target resource: support_002.`
- `evidence/logs/support_replica.log:5`; linking field `resource_id only; no subject link on line`; raw: `2026-09-17T22:00:05Z level=INFO service=support_replica instance=support-eu-03 pod=replica-7c9f trace_id=tr-rp-002 event=contact_query_completed resource_id=support_002 rows=1 latency_ms=23`
- `evidence/logs/support_replica.log:6`; linking field `resource_id only; no subject link on line`; raw: `2026-09-17T22:00:06Z level=WARN service=support_replica instance=support-eu-03 pod=replica-7c9f trace_id=tr-rp-002 event=deletion_marker_check resource_id=support_002 marker_found=false last_write=2026-09-07T10:01:00Z`
## case_15 — `data_flow_9846` (FINDING/REPORT_ACTIVE_DATA_FLOW)
- `system_activity.csv:3387`; linking field `resource_id only; no subject link on line`; raw: `activity_3386,2026-08-22T12:51:10Z,CHECK_DATA_FLOW,deletion_worker,integration_service,data_flow_9846,SUCCESS,Connector status check confirmed that data flow data_flow_9846 remains enabled.`
- `evidence/logs/service_events_ap_south_20260915.log:88`; linking field `resource_id only; no subject link on line`; raw: `2026-09-15T11:58:11Z level=WARN service=integration_service instance=integration-1 pod=integration-95c3 region=eu-central-1 trace_id=tr-9750867 resource_id=data_flow_9846 event=connector_heartbeat enabled=true scheduler_registered=true last_run=success`
## case_15 — `data_flow_9846` (REMEDIATION/DISABLE_DATA_FLOW)
- `system_activity.csv:3387`; linking field `resource_id only; no subject link on line`; raw: `activity_3386,2026-08-22T12:51:10Z,CHECK_DATA_FLOW,deletion_worker,integration_service,data_flow_9846,SUCCESS,Connector status check confirmed that data flow data_flow_9846 remains enabled.`
- `evidence/logs/service_events_ap_south_20260915.log:88`; linking field `resource_id only; no subject link on line`; raw: `2026-09-15T11:58:11Z level=WARN service=integration_service instance=integration-1 pod=integration-95c3 region=eu-central-1 trace_id=tr-9750867 resource_id=data_flow_9846 event=connector_heartbeat enabled=true scheduler_registered=true last_run=success`
## case_15 — `data_flow_9846` (VERIFICATION/VERIFY_DATA_FLOW_DISABLED)
- `system_activity.csv:3387`; linking field `resource_id only; no subject link on line`; raw: `activity_3386,2026-08-22T12:51:10Z,CHECK_DATA_FLOW,deletion_worker,integration_service,data_flow_9846,SUCCESS,Connector status check confirmed that data flow data_flow_9846 remains enabled.`
- `evidence/logs/service_events_ap_south_20260915.log:88`; linking field `resource_id only; no subject link on line`; raw: `2026-09-15T11:58:11Z level=WARN service=integration_service instance=integration-1 pod=integration-95c3 region=eu-central-1 trace_id=tr-9750867 resource_id=data_flow_9846 event=connector_heartbeat enabled=true scheduler_registered=true last_run=success`
## case_17 — `backup_3245` (FINDING/REPORT_RESTORE_RISK)
- `system_activity.csv:3386`; linking field `resource_id only; no subject link on line`; raw: `activity_3385,2026-08-22T12:42:12Z,CHECK_RESTORE_ACCESS,deletion_worker,backup_service,backup_3245,SUCCESS,Restore-access check confirmed that archive backup_3245 can still be restored.`
- `evidence/logs/service_events_ap_south_20260915.log:53`; linking field `resource_id only; no subject link on line`; raw: `2026-09-15T11:54:41Z level=ERROR service=backup_service instance=backup-1 pod=backup-de79 region=eu-west-1 trace_id=tr-8210651 resource_id=backup_3245 event=restore_candidate_evaluated eligible=true deletion_block=false`
## case_17 — `backup_3245` (REMEDIATION/BLOCK_RESTORE)
- `system_activity.csv:3386`; linking field `resource_id only; no subject link on line`; raw: `activity_3385,2026-08-22T12:42:12Z,CHECK_RESTORE_ACCESS,deletion_worker,backup_service,backup_3245,SUCCESS,Restore-access check confirmed that archive backup_3245 can still be restored.`
- `evidence/logs/service_events_ap_south_20260915.log:53`; linking field `resource_id only; no subject link on line`; raw: `2026-09-15T11:54:41Z level=ERROR service=backup_service instance=backup-1 pod=backup-de79 region=eu-west-1 trace_id=tr-8210651 resource_id=backup_3245 event=restore_candidate_evaluated eligible=true deletion_block=false`
## case_17 — `backup_3245` (VERIFICATION/VERIFY_RESTORE_BLOCKED)
- `system_activity.csv:3386`; linking field `resource_id only; no subject link on line`; raw: `activity_3385,2026-08-22T12:42:12Z,CHECK_RESTORE_ACCESS,deletion_worker,backup_service,backup_3245,SUCCESS,Restore-access check confirmed that archive backup_3245 can still be restored.`
- `evidence/logs/service_events_ap_south_20260915.log:53`; linking field `resource_id only; no subject link on line`; raw: `2026-09-15T11:54:41Z level=ERROR service=backup_service instance=backup-1 pod=backup-de79 region=eu-west-1 trace_id=tr-8210651 resource_id=backup_3245 event=restore_candidate_evaluated eligible=true deletion_block=false`

## Requested raw examples

### account_001 (case_01)
- `system_activity.csv:3343`: `activity_3342,2026-08-20T16:41:43Z,DELETE_RECORD,deletion_worker,account_service,account_001,SUCCESS,Deletion worker reported the requested operation as completed. Target resource: account_001.`
### analytics_9406 (case_03)
- `system_activity.csv:3853`: `activity_3852,2026-09-15T10:31:16Z,ANONYMIZE_RECORD,deletion_worker,analytics_platform,analytics_9406,SUCCESS,Policy action completed for analytics_9406.`
- `evidence/logs/resource_lookup_trace_20260926_103856.log:42`: `2026-09-26T09:54:09Z level=DEBUG service=analytics_platform trace_id=rb-095409-021 event=analytics_profile_read_started resource_id=analytics_9406 lookup_key=null`
- `evidence/logs/resource_lookup_trace_20260926_103856.log:43`: `2026-09-26T09:54:09Z level=INFO service=analytics_platform trace_id=rb-095409-021 event=analytics_profile_read_completed resource_id=analytics_9406 customer_reference=null email=null phone=null email_hash=null audience_cohort=general_shopper`
### data_flow_9846 (case_15)
- `system_activity.csv:3387`: `activity_3386,2026-08-22T12:51:10Z,CHECK_DATA_FLOW,deletion_worker,integration_service,data_flow_9846,SUCCESS,Connector status check confirmed that data flow data_flow_9846 remains enabled.`
- `evidence/logs/service_events_ap_south_20260915.log:88`: `2026-09-15T11:58:11Z level=WARN service=integration_service instance=integration-1 pod=integration-95c3 region=eu-central-1 trace_id=tr-9750867 resource_id=data_flow_9846 event=connector_heartbeat enabled=true scheduler_registered=true last_run=success`
### backup_3245 (case_17)
- `system_activity.csv:3386`: `activity_3385,2026-08-22T12:42:12Z,CHECK_RESTORE_ACCESS,deletion_worker,backup_service,backup_3245,SUCCESS,Restore-access check confirmed that archive backup_3245 can still be restored.`
- `evidence/logs/service_events_ap_south_20260915.log:53`: `2026-09-15T11:54:41Z level=ERROR service=backup_service instance=backup-1 pod=backup-de79 region=eu-west-1 trace_id=tr-8210651 resource_id=backup_3245 event=restore_candidate_evaluated eligible=true deletion_block=false`
### support_002 (case_10)
- `system_activity.csv:3597`: `activity_3596,2026-09-02T10:09:01Z,DELETE_RECORD,deletion_worker,support_platform,support_002,SUCCESS,Deletion worker reported the requested operation as completed. Target resource: support_002.`
- `evidence/logs/support_replica.log:5`: `2026-09-17T22:00:05Z level=INFO service=support_replica instance=support-eu-03 pod=replica-7c9f trace_id=tr-rp-002 event=contact_query_completed resource_id=support_002 rows=1 latency_ms=23`
- `evidence/logs/support_replica.log:6`: `2026-09-17T22:00:06Z level=WARN service=support_replica instance=support-eu-03 pod=replica-7c9f trace_id=tr-rp-002 event=deletion_marker_check resource_id=support_002 marker_found=false last_write=2026-09-07T10:01:00Z`
