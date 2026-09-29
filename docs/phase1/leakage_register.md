# Leakage Register

All features are presumed unsafe until their availability is proven.

| Candidate field / concept | Leakage risk | Reason | Phase-1 disposition |
|---|---:|---|---|
| final overall status | Critical | directly contains target outcome | prohibited predictor |
| why_stopped | Critical | created after / at termination | retrospective analysis only |
| actual completion date | Critical | post-start outcome information | prohibited predictor |
| final actual enrollment | High | may reflect realized recruitment | prohibited unless a point-in-time planned value is reconstructed |
| post-start registry updates | High | may encode emerging operational problems | prohibited unless timestamp-filtered |
| results fields | High | generally unavailable at study start | prohibited for baseline predictor |
| planned enrollment | Medium | may be revised after start | allowed only from verified pre-prediction version |
| eligibility criteria | Medium | may be revised after start | allowed only from verified pre-prediction version |

## Leakage principle

A feature is eligible only if its source value is demonstrably available no later than the prediction timestamp used for that trial.
