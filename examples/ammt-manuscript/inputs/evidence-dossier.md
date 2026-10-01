# AMMT IN625 retained-evidence dossier

Date: 2026-10-01. Stage: paper formation. Assignment: independently inspect the existing AMMT case for a journal manuscript, without new model execution. Source root: `C:/Users/Administrator/Documents/ChatGPT/电脑答疑/simulation-agent-mvp/research/reproduction-case/nist-amb2018-02`. All paths below are relative to that root unless given otherwise. This dossier supplies facts and claim boundaries to the coordinator; it does not promote scientific claims or grant validation.

## Contract and inspection performed

The contracted question was what the retained AMMT IN625 calculations actually establish about geometry, operating-condition response and high-temperature constitutive continuations, and what is missing for an Additive Manufacturing-level draft. The inspection covered original Lane experimental methods, the original Kollmannsberger author-source equations/methods, the actual frozen FiPy solver and factorial wrapper, their material and measurement dependencies, current CSV/JSON results, calibration history/provenance, numerical benchmark and neighborhood records, and retained arrays for all six production runs. No solver module was imported; no PDE was assembled or solved; source files and prior runs were not changed.

The helper `inspect_evidence.py` reads only retained artifacts. It wrote `verified-data.json`, checked six executed-source/dependency bindings, finite temperatures and liquid-fraction bounds, integrated half-domain Gaussian power, reconstructed the reported length from saved centerline arrays, and checked comparison-ratio/factorial algebra. Its first execution encountered a UTF-8 BOM in a CSV header; the single correction changed the reader to `utf-8-sig`, after which all checks passed. The earlier console extraction had a Windows output-encoding issue and was repeated with UTF-8 output. These are inspection-tool issues and do not alter scientific evidence. The production arrays have not been modified or re-fitted.

## What can be written now

The retained evidence supports an explicitly bounded computational study: a circular-Gaussian, isotropic-conduction, equilibrium-phase-change model fitted to one AMMT B length proxy; fixed-parameter, nonblind comparisons at A/C; and a deterministic, fixed-B four-corner contrast of high-temperature table-continuation rules. It supports a persistent wide/shallow model discrepancy, and a model-internal explanation of the large rear-tail response to the k-continuation choice. It does not support blanket physical validation, identification of real liquid properties, precise imaging replay, flow/evaporation causality, or generalization to powder layers, multiple tracks/layers or other machines.

The actual status in `report/current-results.json` is `APPLICATION_RESEARCH_PACKAGE_COMPLETE`, with `physical_validation_status=NOT_ESTABLISHED_BY_CALIBRATION_OR_PROCESS_COMPLETION`. The six `result.json` files retain `science_gate=PENDING_APPLICATION_REVIEW`; subsequent bounded reviews and current-package dispositions must be cited with their scope, rather than rewriting these historical records as an unrestricted solver PASS. This inspection independently confirms numerical consistency of saved artifacts but cannot create missing experimental evidence.

## Actual model, equations and conditions

### The method belongs to the FiPy candidate

The production candidate is `FIPY_APPLICATION_MOVING_FRAME_V5`. Its implementation is the 40,338-byte `verification/fipy-application-B-cal-05-r13/frozen-solver-source.py`; the corresponding frozen primary code was checked in all six run directories. `reconstruction-contract.md` and `solver/README.md` still describe a legacy FEniCSx P1/Backward-Euler candidate. That legacy numerical method must not be presented as the method used for the current tables. Likewise, old FEniCSx or native-transient checks do not automatically verify this FiPy nonlinear discretization.

The laboratory-frame balance is

\[
\partial_t H(T)=\nabla\!\cdot[k(T)\nabla T],\qquad
H(T)=\rho\left[\int_{T_0}^{T}c_p(s)\,ds+\mathcal L f(T)\right].
\]

The retained solution assumes a locally quasi-steady translating region. With \(\xi=x-vt\) and \(\mathbf u=(-v,0,0)\),

\[
\nabla\!\cdot(\mathbf uH-k\nabla T)=0.
\]

This coordinate enthalpy transport describes stationary material passing through the laser coordinate system. It is not liquid convection. The unknown is \(U=H/C_0\), where \(C_0=\rho(402\;\mathrm{J\,kg^{-1}K^{-1}})=3{,}392{,}880\;\mathrm{J\,m^{-3}K^{-1}}\). \(U\) has units K but is not the temperature. The internal diffusion face coefficient is \(D_f=k_f\Delta T/(C_0\Delta U)\), units \(\mathrm{m^2\,s^{-1}}\), with the positive derivative limit near zero differences. Harmonic face conductivity is provided by FiPy. The source is integrated as a boundary power and represented as an equivalent top-control-volume source. Source locators: frozen solver lines 327–377 and 477–508; `solver/native_fv_enthalpy.py` lines 31–150; manuscript equations in `report/ammt-multi-agent-stage-report.tex` lines 481–588.

Material constants are \(\rho=8440\;\mathrm{kg\,m^{-3}}\), \(\mathcal L=280000\;\mathrm{J\,kg^{-1}}\), \(T_s=1290^\circ\mathrm C\), \(T_l=1350^\circ\mathrm C\), and cold reference \(T_0=25^\circ\mathrm C\). The model liquid fraction is 0 below \(T_s\), \((T-T_s)/(T_l-T_s)\) in the mushy interval, and 1 at/above \(T_l\). The enthalpy is an exact piecewise quadratic integral with an analytic, positive-branch inverse; latent heat enters H, rather than an inconsistent replacement by a frozen pointwise heat capacity. Inside the interval, \(c_{p,\mathrm{eff}}=c_p+4666.666666666667\;\mathrm{J\,kg^{-1}K^{-1}}\).

The general-alloy bulletin data in `material-properties.csv` supply tabulated cp from −18 to 1093 °C and k from −157 to 982 °C. Values are interpolated linearly between knots. The baseline continues the final slopes above the individual endpoints; the H factors hold the final values, cp=670 J/(kg K) and k=25.2 W/(m K), respectively. No retained measurement establishes these high-temperature continuations as actual properties of the test coupon. Constant density/latent heat and the equilibrium linear phase fraction are closures. Every cell at \(T\geq T_s\) is above both table endpoints; the entire hot/mushy/liquid mechanism uses extrapolated or held model properties. The exact table rows are preserved in `verified-data.json`.

The physical referent is bare IN625 plate single-track scanning on AMMT: A \((P,v)=(137.9\;\mathrm W,0.4\;\mathrm{m\,s^{-1}})\), B \((179.2,0.8)\), C \((179.2,1.2)\). The circular Gaussian is

\[
q_L(\xi,y)=\frac{2\eta P}{\pi w^2}\exp[-2(\xi^2+y^2)/w^2],\qquad w=85\;\mu\mathrm m,
\]

using reported D4σ=170 μm. Its full-plane integral is ηP; its modeled y≥0 half-domain receives ηP/2. The erf-integrated rectangle loading was independently recovered from stored `top_q_W_m2` and face coordinates for all six runs. B has half source power 25.89931473206377 W. The Gaussian shape is a reconstruction assumption, not the measured 2D power map used by the original numerical paper.

All six production runs have 902,664 cells, shape 199×56×81, near-source spacing 4×3×1 μm, core intervals ξ=[−0.48,0.16] mm, y=[0,0.12] mm, z=[−0.06,0] mm, and outer spacings graded by 1.22 up to 25 μm. The domain is ξ=[−1,0.35] mm, y=[0,0.36] mm, z=[−0.30,0] mm. Boundaries are: cold material inflow U=0 at positive ξ; zero diffusive gradient and material advective outflow at negative ξ; mirror symmetry at y=0; adiabatic outer-y and bottom; Gaussian top flux with adiabatic remainder. A warm field is a nonlinear initial guess, not a transient initial condition. The production solve includes no radiative or natural-convective feedback.

FiPy 4.0.3 assembles diffusion and `ExponentialConvectionTerm`; the actual production choice is SciPy Anderson acceleration of the frozen-coefficient solve residual, with SciPy GMRES (tolerance 2×10⁻⁹, restart 80, legacy inner-iteration cap 800), PyAMG Ruge–Stuben preconditioning and one BLAS thread. Actual solver environment records are Python 3.13.5, NumPy 2.5.3, SciPy 1.18.1, PyAMG 5.3.0. The script retains other nonlinear methods, but their presence does not establish that these production runs used them.

### Observables and the measurement gap

Model L is the separation of the two \(T_s\) crossings of the reconstructed top symmetry-centerline temperature. The crossings are linearly interpolated; the source must belong to the single hot interval, with no endpoint truncation. Surface recovery uses the integrated conductivity primitive: \(K(T_{\mathrm{surface}})-K(T_{\mathrm{top-cell}})=q\Delta z/2\), \(K'=k\). The symmetry plane is recovered by an even quadratic extension. Source locators: frozen solver lines 75–105, 183–201; material lines 147–150.

Model W/D are the source-connected fusion envelope of \(\max_\xi T(\xi,y,z)\geq T_s\), interpreted as material passage through the stationary solution. Symmetry and surface are restored separately for each ξ slice, each slice is bilinearly interpolated to observation coordinates, and only then is the maximum taken over ξ. Width is twice the positive-y extent; depth is minus the lowest z. A four-neighbor component containing y=0,z=0 must be nonempty and untruncated. The 0.5 μm geometry pitch is interpolation sampling, not the heat-field resolution. `solver/passage_observer.py` contains this primary observer; frozen solver lines 183–302 preserve the older nodal-max proxy only as a sensitivity observable. The saved `yz_Tmax_C` array originates in the older nodal-max construction inside `measures`; it is not by itself an exact substitute for the primary passage observer. Manuscript figure extraction should use the retained primary observer/result or reproduce its stated order, not silently treat every stored `Tmax` label as equivalent.

Lane's actual length method differs. `lane-2020-experiment.md` §2.3, lines 675–747: camera signal is calibrated through Sakuma–Hattori; the solidification location is the minimum of the second derivative of the radiance profile; its emittance is estimated by assigning 1290 °C; the front is the corresponding calibrated-temperature intersection. Thus the experimental length is \(|x_{\mathrm{front}}-x_{\mathrm{freeze}}|\), not an untouched temperature field's two-solidus crossing length. The present model does not apply radiance/emittance, pixel averaging, PSF, oblique-view projection, 20 μs integration or motion blur. B η is therefore an effective source/model/operator parameter, not an identified absorptivity constant.

## Calibration, data roles and exact comparison

The successful B calibration points are (η,L/μm): (0.2,234.56922314200827), (0.4,511.68225620654886), (0.2898050701419095,359.95786945492335), (0.285314816634814,354.22476866406913), (0.2890548519203547,359.1575457177625). The failed cal-03 run did not enter the objective; its repaired accepted-checkpoint successor did. The frozen effective η=0.2890548519203547 yields residual +0.1575457177625026 μm. The local/bracket derivative is 1276.787776412803 μm per η; propagation of B's reported expanded U gives Δη=0.016651161918021334. This is a local sensitivity calculation, not a posterior parameter distribution or full prediction uncertainty. The sampled points establish a local monotone bracket, not global uniqueness over [0,1]. The original contract's global-root requirement is stronger than the retained sampled evidence.

`verification/fipy-application-calibration-r13/provenance-audit.json` records PASS in `RETAINED_ARTIFACTS_ONLY_NO_DRIVER_OR_SOLVER_IMPORT` mode. Its executed driver snapshot is distinguished from a post-execution live-driver patch. The scalar objective read only `validation/b-length-calibration-only.json`. All A/B/C public targets were already known to the research team; therefore A/C are nonblind, retrospective, fixed-parameter condition comparisons. B W/D are post-calibration diagnostics and did not enter the objective. No claim of untouched blind validation is justified.

| Case | QoI | Model μm | Experimental mean μm | Separate Lane U(k=2) μm | Signed Δ/U |
|---|---|---:|---:|---:|---:|
| A | L | 309.8856792638423 | 300 | 11.91 | +0.8300318441513259 |
| A | W | 153.36005335598344 | 147.9 | 6.42 | +0.8504756006204724 |
| A | D | 40.46931231766381 | 42.5 | 4.49 | −0.4522689715670809 |
| B | L, fitted | 359.1575457177625 | 359 | 21.26 | +0.007410428869355719 |
| B | W | 143.0406226383922 | 123.5 | 6.30 | +3.101686133078126 |
| B | D | 31.12034988767346 | 36 | 3.97 | −1.2291310106615971 |
| C | L | 320.6313629678825 | 370 | 32.57 | −1.5157702496812244 |
| C | W | 129.04618690578758 | 106 | 4.48 | +5.144238148613298 |
| C | D | 22.044541383670747 | 29.6 | 3.26 | −2.3176253424322866 |

Source: `report/experimental-comparison.csv`, checked against saved results. Three A differences are within the source expanded-U scale. B W/D and all three C differences are outside. The fitted B L contributes no independent corroboration. The comparison statistic is a signed difference divided by experimental U alone: it is not a z score, significance test, likelihood, or the combined-uncertainty \(E_n\) proposed in the old reconstruction contract. Numerical, calibration, input and operator uncertainty have not been combined into those nine values.

The exact current W/D targets originate in the current NIST challenge website Section 2/Table 2, saved at `validation/nist-data/amb2018-02-mp-xsection-official.html`, and `validation/ammt-width-depth-provenance.json`. These are AMMT-100 μs trace class values. Lane Table 4 subsequently combines AMMT-100 μs and AMMT-20 μs cross-sections and reports integer displayed means (A 148/42, B 123/36, C 106/30). Lane U is a separately sourced measurement-uncertainty scale, not uncertainty jointly reported with these current NIST decimal values. The original numerical article gives C depth 29.5 μm, the current NIST table 29.6, and Lane's integer 30; preserve the source representations. Do not silently substitute 29.5 or pretend that `36.0`/`106.0` establishes a tenth-micrometre observed digit. The earlier source-precision decision explicitly required a versioned contract revision for formal scoring; the present descriptive package must not be called that revision's completed formal validation.

### Statistical meaning of U and replication

Lane §4, equations (12)/(13) and Tables 5–7, reports expanded uncertainty \(U=k u_c\), k=2. Standard components are converted to length and added in quadrature **without correlations**. Approximately 95% coverage under suitable distribution/effective-degrees assumptions is the usual meaning of k=2; these values are not directly observed ±2 specimen SD, nor solely confidence intervals for the mean. Do not claim exact 95% joint nine-QoI coverage.

Length components include camera calibration, signal digitization/noise, pixel size, Type-B blur estimates and standard uncertainty of the pooled-frame mean. Lane Table 4 has AMMT length frame counts A/B/C=19/10/7; frames are correlated within tracks and are not independent specimens. For N<30 the source scales σ/√N using a Student-t value for 68.3% coverage of its mean component. That component is only one contributor to U.

Cross-section uncertainty includes 0.5 μm optical-resolution standard uncertainty, 0.372 μm selection repeatability, estimated longitudinal variability (2% width and 5% depth, Type B), and the mean component. Current NIST microscopic tracks are A/B/C=3/3/4; the 9/9/12 measurements include repeated selections. The NIST class SD is across displayed trace means: A W/D SD 3.7/1.7 μm, B 6.5/1.9, C 1.4/0.6. It is distinct from Lane U. The original boundary-pick coordinates and raw AMMT thermography series are absent; the available MAT/XLSX are CBM. This limits reaggregation, covariance analysis and full measurement-operator checking. Source locators: Lane lines 838–870, 946–973, 979–1036; `validation/replication-audit.json` interpretation; primary NIST table and provenance audit.

L and W/D are condition-level comparisons across imaging/microscopy populations, not the simultaneous three-dimensional shape of one track. Ratios of W/D means and B→C nominal-percent changes are descriptive; their uncertainties/covariances have not been propagated. Lane explicitly labels cooling rates exemplar data, unsuitable as reference/calibration, in lines 870 and 1056–1060.

## Six unique production runs and numerical adequacy

The union of A/B/C and B's four corners is six, since baseline B is also LL. They are deterministic computations, not six experimental replicates. Historical calibration/refinement/probe runs exist beyond this production union.

| Run directory under verification | Use | Iterations | L1 residual / absorbed half power | Signed global balance | Full correction °C |
|---|---|---:|---:|---:|---:|
| fipy-application-A-frozen-r13 | A | 74 | 1.2841515517804504e−7 | −3.05007776843657e−11 | 2.6300048602934112e−5 |
| fipy-application-B-cal-05-r13 | B=LL | 52 | 1.1101784994680737e−7 | −6.034533007221461e−11 | 1.0866614275073516e−5 |
| fipy-application-C-frozen-r13 | C | 91 | 9.625153697950313e−8 | −4.125276107958146e−11 | 1.4760801605007146e−5 |
| fipy-application-B-highT-frozen-r14 | HH | 56 | 6.896702666570753e−8 | +1.7410403719387755e−11 | 1.6324755279129022e−5 |
| fipy-application-B-khold-cplinear-r15 | HL | 59 | 7.83309389411468e−8 | +1.4339625622113726e−11 | 2.067851482934202e−5 |
| fipy-application-B-klinear-cphold-r15 | LH | 56 | 1.3149740366546284e−7 | −5.996782710948353e−11 | 2.1253455088299233e−5 |

The implemented gates are L1<2e−5, absolute balance<2e−5, full frozen-coefficient correction<0.002 °C, finite fields, lower temperature≥24.9 °C, positive constitutive diffusion and qualified/untruncated observers. All six final T minima are 25.000000000000004 °C and retained liquid fractions are in [0,1]. The inspection found each frozen primary/wrapper snapshot and current shared material/observer/CSV dependency matches its executed manifest binding. `mechanism-fields.npz` is present locally for all six. This is file/source and algebraic evidence, not a fresh runtime replay.

Important verification facts and boundaries:

- **Local residual is required as well as global energy balance.** The old FiPy cached-stencil defect let differing local nonlinear equations share near-zero global signed balance. `collaboration/native61-fipy-v3-factory-review-r2.json` records old fresh/current-coefficient L1=0.050645498451027796, history-cached L1=0.001386915169723153, and vector difference 0.05050950085001335, despite signed global sums around 5.13e−9. The executed current source recreates diffusion/exponential terms after each D update; corrected cold/warm histories agree exactly. Old r5/r6/r7 results are historical diagnostics, not the formal baseline.
- **Analytical benchmark is constant-property only.** `verification/native61-constant-gaussian-frame-r1/qoi-analytic-report.json` gives analytic L/W/D=407.53487223490673/153.2928547567595/34.83571358212982 μm and FiPy=408.0998265780106/153.5840201596997/34.66185562495091 μm, relative differences +0.138627%/+0.189941%/−0.499080%. It checks the Gaussian moving-source and geometry treatment for this simpler problem, not latent nonlinear convergence or NIST validation. Retained near-field point/volume-averaged comparisons differ by operator; graded far-field mismatch is larger.
- **Spatial sensitivities are measured contrasts.** At η=0.2, x=8→4→2 μm with y/z=6/2 gives L=232.4851772458446→234.72285232447706→234.80767870785073 μm; W=118.86009778117878→118.90031904935856→118.89401782915274; D=20.310481659454812→20.420173104523215→20.459175523689403. Independent y/z refinements and domain extension are in the JSON. These are not a full 3D asymptotic refinement sequence or a certified absolute error bound.
- **Frozen-η follow-up addresses some local transfer of accuracy.** B x4→2 (y/z=3/1) changes L/W/D by +0.3608485709389697/−0.008773070678500972/+0.04062989049403498 μm. C gives +0.19932572613288357/−0.02886121420928589/+0.044856308883332474 μm. These are ≤0.204% for the three geometry QoIs and much smaller than the B/C experimental residuals. A/B expanded-domain differences are ≤2.91864068913128e−6 μm. See `verification/fipy-application-neighborhood-r14/summary.json`. This supports bounded shape-discrepancy discussion, but does not establish calibrated y/z convergence or branch-specific submicrometre factorial accuracy.
- **Steady approximation is partly checked, not universally certified.** `verification/native61-steady-transient-retained-r1/report.json` compares η=0.2 B to an older transient h10 solution with different truncation/mesh/surface reconstruction. L differs by 1.7279880768049513 μm; cell/surface T RMS differences are 19.6403/32.8059 °C. The record explicitly grants only rough local stationary consistency, not formal numerical release. There is no current six-run time-step convergence claim: the production equations are steady; historical transient dt tests are not substitutes for steady-assumption adequacy at A/C and the constitutive corners.
- **Radiation is a screening calculation.** Fixed-field blackbody ε=1, no-feedback top losses in B corners are 0.0993%–0.1801% of absorbed power. This suggests a small top-loss scale within the retained state, but is not a solved radiation/convective-feedback envelope. It cannot alone prove those boundary closures at every use.

Thus the numerical evidence is sufficient to prevent nonlinear nonconvergence or the inspected axial/domain changes from being used as the main explanation of tens-of-micrometre B/C discrepancies. It is not evidence that every unresolved submicrometre interaction, real phase-front thickness or peak temperature is accurately predicted.

## Condition trends and mechanism evidence

With fixed η, absorbed line energy A/B/C=99.65166019954228/64.74828683015944/43.16552455343963 J/m; source-radius residence w/v=212.5/106.25/70.83333333333334 μs. A→B changes power and speed simultaneously; it cannot isolate speed. B→C fixes 179.2 W and raises speed by 50%. Model W shrinks 9.783539441087763%, whereas nominal experimental W shrinks 14.17004048582996%; model D shrinks 29.163581183248755%, versus 17.77777777777777%. Model W/D ratios A/B/C=3.7895393959794506/4.596369358143031/5.853883946135397; nominal experimental ratios=3.48/3.4305555555555554/3.5810810810810807. This establishes increasing modeled wide/shallow discrepancy across the stated conditions, not its unique physical cause.

Experimental B→C L rises only 11 μm; a zero-correlation quadrature of their reported expanded-U scales is 38.89463330589453 μm. The sign of that measured nominal length trend is unresolved at this scale. The model predicts L decrease of 38.52618274987998 μm. C's individual −49.3686370321175 μm discrepancy is still outside C U=32.57 μm. Do not equate those distinct observations or claim a statistically demonstrated opposite trend.

The rear liquidus-to-solidus centerline spans A/B/C are 48.29519038375836/80.26402604458121/80.79140265237265 μm. Dividing by speed gives passage times 120.7379759593959/100.3300325557265/67.32616887697722 μs and model average cooling rates 0.4969438946051072/0.5980263184572783/0.8911839333920206 MK/s across 1350→1290 °C. These are model definitions; Lane measures an example 1290→1190 °C cooling interval and excludes it as reference data. Similar B/C spatial spans do not imply similar material cooling times.

### Fixed-B 2×2 continuation contrast

Coding: first letter k, second cp; L=linear continuation, H=hold final table value. η, P/v, phase law, beam, mesh, BC and observer are held fixed. LL reuses frozen B, HH reuses r14; only HL/LH are new r15 solves. The frozen r15 wrapper `frozen-factorial-wrapper.py` composes thermal k/K/surface recovery from the k branch and storage cp/H/T(H) from the cp branch; lines 28–58, 125–171 establish that mapping. Its preregistration recorded exact LL/HH legacy equivalence and mixed inverse round-trip checks. Current `solver/run_constitutive_factorial.py` includes later collection changes; cite executed wrapper snapshots for run method and current collection source for derived tables.

| Corner | L μm | W μm | D μm | Surface peak °C |
|---|---:|---:|---:|---:|
| LL | 359.1575457177625 | 143.0406226383922 | 31.12034988767346 | 2697.0732343382333 |
| HL | 402.3712581813177 | 143.15007404634164 | 30.092012429039947 | 3506.5728926812694 |
| LH | 352.9886879571668 | 143.71622129720419 | 31.61342715629935 | 2756.354569813648 |
| HH | 393.44045830101044 | 143.7869176712329 | 30.797065270818912 | 3720.946596884735 |

For Q define k-only at cp-L=QHL−QLL; cp-only at k-L=QLH−QLL; interaction I=QHH−QHL−QLH+QLL; joint=QHH−QLL. These deterministic finite contrasts have no sampling error model or statistical-significance interpretation. Average main effects are averages over the other factor's two settings, not regression estimates from replicated experiments.

| QoI | k-only | cp-only | Interaction | Joint HH−LL | k average main | cp average main |
|---|---:|---:|---:|---:|---:|---:|
| L μm | +43.213712463555225 | −6.168857760595699 | −2.761942119711591 | +34.282912583247935 | +41.83274140369943 | −7.549828820451495 |
| W μm | +0.10945140794945019 | +0.6755986588119924 | −0.038755033920722326 | +0.7462950328407203 | +0.09007389098908902 | +0.6562211418516313 |
| D μm | −1.0283374586335121 | +0.4930772686258891 | +0.2119755731530759 | −0.3232846168545471 | −0.9223496720569742 | +0.599065055202427 |

At k-only hold, rear Ts/Tl coordinates move −42.487288722914684/−43.500431573763166 μm and front Ts moves +0.726423740640513 μm. The rear phase span changes −1.013142850848439 μm. At cp-only hold, rear Ts/Tl move +6.223377970654269/+6.5302808771700995 μm; front Ts moves +0.05452021005854846 μm; rear phase span changes +0.3069029065158446 μm. The large length effects therefore predominantly represent common rear-boundary translation rather than marked widening of the mushy span.

Matched T=1320 °C: linear versus held k is 32.508108108108104 versus 25.2 W/(m K), a −22.48% change; latent-inclusive effective cp is 5387.792792792793 versus 5336.666666666667 J/(kg K), only approximately −0.95%. The mushy x-face median coordinate-transport/diffusion Pe increases LL→HL from 4.436821677351234 to 5.77334501159608; LH gives 4.390000426125581. This corroborates reduced modeled diffusion relative to material-coordinate transport as the source of rear-tail change. It does not observe a melt flow or identify true high-temperature conductivity.

The net small D change conceals opposing single-factor responses. All four corners still overpredict W and underpredict D relative to B. The alternatives have not repaired geometry. For L the ~34–43 μm response is much larger than retained B's 0.361 μm axial sensitivity. The 0.039 μm W interaction and 0.090 μm k mean effect deserve descriptive wording: branch-specific convergence and an error estimate were not performed, so their fine rankings should not be claimed with the same precision as the major L response. Temperature-selected control-volume energy/flux budgets are state-dependent regions, not fixed-material-volume causal estimands. Their balance closure establishes accounting consistency, not the unique real transport mechanism.

Model peaks 2420–3721 °C are internal states of a model without evaporation, liquid flow or free-surface response. They cannot be used as measured liquid temperatures or evidence of keyholing/evaporation. Likewise the Ts→Tl front crossings can be subcell interpolations; they are not resolved physical front thicknesses.

## Original numerical paper and competing explanations

Original source: `arxiv-1903.09076-source/gouverningEquations.tex` gives the transient nonlinear heat/latent balance, radiation boundary \(q^r=\sigma\epsilon(T_e^4-T^4)\), and a phase-change smoothing law containing a calibration parameter S. The archived author equation is not sufficiently explicit to treat the present saturated linear phase fraction as an exact reproduction. The current model deliberately adopts its own closed fraction law and table values; k's source endpoint is 982 °C, whereas the paper describes measured k up to 871 °C. The exact AMMT 2D beam field and author high-temperature calibration cannot be uniquely reconstructed here.

`modelVerification.tex` lines 322–364: the paper's AMMT model uses the measured beam profile, calibrated η=0.086, and isotropic predictions A=(301,119,52), B=(360,103,42), C=(348,91,32) μm. It is narrow/deep relative to its experimental table; the largest reported geometry deviation is 19.3%. Lines 385–426 replace scalar k with diag(kθx,kθy,kθz), deviations from unity above 871 °C, and B-fitted θ=(1,1.4,0.9). Fixed A/C results, lines 437–439, are (304,146.4,44.6), B=(362,123.7,36.1), C=(346,105.1,27.3). Those later tensor results are retrospectively within the separately sourced Lane U scales; this is our scale comparison, not a coverage claim made by the original paper.

The paper supplies an implementable precedent for effective directional heat transport. Its isotropic bias has the opposite sign from the current Gaussian model. Consequently neither η=0.086 nor θ=(1,1.4,0.9) can be transplanted as physical constants. Plausible competing sources of present residuals include the unreplayed beam distribution, high-temperature/storage/phase closures, camera/fusion measurement operators and omitted directional liquid heat transport. The present factorial distinguishes two constitutive continuation rules within the fixed model, not these alternatives experimentally. A physically named mechanism such as Marangoni flow remains unidentified.

## Missing evidence and claim-scoped draft recommendations

An Additive Manufacturing-level draft can honestly be written from these files, but its argument must be a bounded sensitivity/discrepancy study. The coordinator must assess novelty against current literature and journal expectations; existing completed workflow/provenance is not a scientific contribution by itself. Evidence gaps affecting stronger candidate claims are:

1. **Predictive validation across independent conditions:** all published A/C data were visible; no new or untouched condition/specimen campaign exists. The η interval is incomplete, calibration uncertainty is not propagated to geometry, and current ratio scores omit numerical/input/operator components. Needed only if making quantitative predictive or coverage claims: new independent tracks/conditions with defined data roles and a combined uncertainty model.
2. **Exact experimental comparison:** missing raw AMMT thermography, microscope boundary-pick data and camera measurement replay; exact NIST target means and Lane combined-class U are separately sourced. Needed for operator-aligned validation: acquisition/reconstruction of those data and imaging operators. Current wording should say proxy/class comparison.
3. **General constitutive causality:** only one fixed B factorial and two continuation options exist; no cross-speed factorial, continuous-property uncertainty, parameter identifiability, beam-shape contrast or liquid-flow contrast. The result identifies model sensitivity, not real material values or the unique physical explanation of residuals.
4. **Submicrometre effects/peak/phase-front precision:** current axial/domain studies lack branch-specific multidirectional convergence; no calibrated y/z refinement or formal absolute-error estimate. This does not block descriptive major-tail results, but limits small-effect rankings, subcell phase spans and asserted temperature accuracy. A cheaper discriminating extension would be one preregistered matched-physics branch refinement targeting the specific small QoI, rather than refining all six runs.
5. **Boundary and steady assumptions outside inspected use:** retained transient comparison is old η=0.2 B and approximate; radiation is fixed-state/no-feedback; no natural-convection feedback envelope or experimentally established steady error for A/C/corners. These limit broad applicability. They do not justify concealing current large geometry discrepancies.
6. **Method novelty or superiority:** FiPy, exponential FV, Anderson/AMG and analytical source benchmarks are established methods. Actual acceleration timing is valuable implementation evidence, but comparing unlike warm starts/versions is not a universal performance claim. A journal manuscript needs a defensible scientific gap and comparison with relevant contemporary source/transport models, not an automatic assertion of novelty from this implementation.

The cheapest manuscript-first decision is to keep the current scientific scope: scalar conduction/phase-change closures, source/proxy calibration, fixed-parameter discrepancies, and model-internal tail decomposition. If that contribution is insufficient for the intended journal, the next consequential simulation should be a new bounded mechanism contrast chosen to distinguish beam/operator/transport alternatives, with data roles fixed before fitting. No new computations were authorized or performed by this specialist.

## Delivery provenance and return

`verified-data.json` contains exact numerical values, source-root paths, six manifest/array/source checks, constants/table rows, all nine comparisons, both factorial-effect definitions, finite-corner data, descriptive B→C values, and numerical evidence with stated scope. `inspect_evidence.py` is the read-only extraction/check recipe. This dossier and those files are the only writes under the assigned evidence directory. Major claims are supported only to the bounds described above; the coordinator must independently interpret and disposition them. The contracted inspection question has been answered; no extension or solver rerun is requested.
