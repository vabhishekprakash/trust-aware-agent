# Log-probability text mismatch, before any fit

The draft was regenerated at temperature 0 with logprobs on. When its text differs from the graded draft, the logprob features describe a different output than the label does.

## Mismatch rate

- Pooled: 44/134 (33%) of items mismatched.
- Decisive stratum (answerable, evidence retrieved): 20/50 (40%) mismatched; matched subset there is 20 right against 10 wrong.
- Per bucket: answerable 24/62 (39%), ambiguous 6/9 (67%), unanswerable 4/34 (12%), false_premise 10/29 (34%).

## Feature means by label on the matched subset alone

Pooled matched subset, then the matched part of the decisive stratum. Log-probability features first, then a few others for scale.

| feature | matched, label 1 | matched, label 0 | decisive matched, label 1 | decisive matched, label 0 |
|---|---|---|---|---|
| lp_mean | -0.096 (sd 0.133, n=50) | -0.174 (sd 0.148, n=40) | -0.136 (sd 0.132, n=20) | -0.140 (sd 0.145, n=10) |
| lp_min | -0.844 (sd 1.096, n=50) | -1.325 (sd 1.136, n=40) | -1.386 (sd 1.137, n=20) | -1.146 (sd 1.209, n=10) |
| lp_p10 | -0.377 (sd 0.575, n=50) | -0.673 (sd 0.626, n=40) | -0.452 (sd 0.509, n=20) | -0.424 (sd 0.543, n=10) |
| lp_share_below_1 | 0.029 (sd 0.055, n=50) | 0.049 (sd 0.063, n=40) | 0.043 (sd 0.057, n=20) | 0.034 (sd 0.053, n=10) |
| lp_first | -0.071 (sd 0.164, n=50) | -0.201 (sd 0.267, n=40) | -0.122 (sd 0.213, n=20) | -0.201 (sd 0.294, n=10) |
| lp_tokens | 17.040 (sd 16.062, n=50) | 25.950 (sd 24.893, n=40) | 28.500 (sd 16.728, n=20) | 20.900 (sd 13.412, n=10) |
| lexical_support_top1 | 0.406 (sd 0.338, n=50) | 0.493 (sd 0.253, n=40) | 0.728 (sd 0.212, n=20) | 0.550 (sd 0.247, n=10) |
| cosine_top1 | 0.616 (sd 0.142, n=50) | 0.695 (sd 0.133, n=40) | 0.758 (sd 0.076, n=20) | 0.732 (sd 0.110, n=10) |
| vc_confidence | 45.000 (sd 48.708, n=50) | 69.000 (sd 43.297, n=40) | 100.000 (sd 0.000, n=20) | 88.500 (sd 31.451, n=10) |
| sa_max_to_draft | 0.934 (sd 0.149, n=50) | 0.776 (sd 0.278, n=40) | 0.878 (sd 0.181, n=20) | 0.784 (sd 0.300, n=10) |
| sa_form_agree | 0.940 (sd 0.129, n=50) | 0.870 (sd 0.190, n=40) | 0.960 (sd 0.082, n=20) | 0.960 (sd 0.084, n=10) |
| action_answer | 0.420 (sd 0.499, n=50) | 0.525 (sd 0.506, n=40) | 1.000 (sd 0.000, n=20) | 0.500 (sd 0.527, n=10) |

## For comparison, all items, decisive stratum

| feature | label 1 | label 0 |
|---|---|---|
| lp_mean | -0.180 (sd 0.126, n=33) | -0.188 (sd 0.154, n=17) |
| lp_min | -1.780 (sd 1.083, n=33) | -1.376 (sd 1.075, n=17) |
| lp_p10 | -0.617 (sd 0.493, n=33) | -0.679 (sd 0.666, n=17) |
| lp_share_below_1 | 0.060 (sd 0.055, n=33) | 0.057 (sd 0.064, n=17) |
| lp_first | -0.162 (sd 0.236, n=33) | -0.276 (sd 0.282, n=17) |
| lp_tokens | 34.667 (sd 21.163, n=33) | 26.353 (sd 16.248, n=17) |
