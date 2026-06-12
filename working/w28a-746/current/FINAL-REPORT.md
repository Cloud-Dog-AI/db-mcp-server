# W28A-746 Final Report

## Evidence Matrix
| Requirement | Raw artefact | Raw value observed | Verification command | Pass |
|---|---|---|---|---|
| Build, deploy, and prove live on dbmcpserver0 | raw/terraform-apply.log; raw/live/live-health-and-identity.log | Terraform recreated dbmcpserver0 and live health stayed green | terraform apply; curl health | PASS |
| main == deployed source proof | raw/live/main-deployed-proof.log | origin/main, local image label, remote image label, and running container revision all equal 9f1e158a | git rev-parse; docker inspect | PASS |
| IDAM b-method and cascade proof | raw/tests/smoke.log | W28A-746 smoke tests passed | pytest tests/smoke/test_w28a746_b_method_idam.py | PASS |
| Live contract proof | raw/live/live-e2e-pytest-rerun2.log | 2 passed | pytest tests/e2e/test_w28a746_live_preprod_contract.py | PASS |
| WebUI browser proof | preprod-webui-smoke/screenshot-manifest.tsv | 20 screenshots captured; fatal console/network count zero after classification | Playwright Chromium smoke | PASS |

## Close Gate
HAVE_ALL_REQUIREMENTS_BEEN_MET: YES

Sequence 7 / W28A-746 is delivered for db-mcp-server only. Accepted W28A-732-R5 and W28A-871-R2 ancestry is preserved. The deployed container on dbmcpserver0 carries OCI revision 9f1e158a1c3e37748298aa35af950972f287eff6, matching the pushed source main at deployment time. Subsequent evidence-only commits do not alter runtime source paths used by the deployed image.
