# AMMT evidence → argument → concise prose

This is a new, manually authored local revision exercise using the retained evidence in `../ammt-manuscript/inputs/evidence-dossier.md` and `verified-data.json`. The before paragraphs are deliberately constructed defects, not quotations from the user's manuscript. The after paragraphs are actual prose candidates, with no new solver or measurement execution. They demonstrate what to check; they are not desired answers supplied to the forward-use model. The historical AMMT manuscript and reports are untouched.

## Methods: calibration and comparison

**Before (constructed defect).** An evaluation of model accuracy was performed by comparison with experimental measurements. Absorptivity was determined by fitting the melt-pool length at B. The validated model was then used to predict the other operating conditions.

**After.** We fitted the effective source coefficient to the reported melt-pool length at condition B and retained it for the comparisons at A and C. These condition comparisons assess the response of the conduction model to changes in power and scan speed. The A and C targets were already known to the research team, so they are retrospective comparisons with fixed parameters. The fitted coefficient also incorporates differences between the assumed source and the experimental observation procedure; it does not identify material absorptivity independently.

**Evidence and reasoning.** Dossier sections “Calibration, data roles and exact comparison” and “Observables and the measurement gap” define these roles. The reader needs to know what fitting establishes and what the following comparison adds. Direct operations replace the reporting shell. “Effective,” “already known” and the observation-procedure distinction preserve scientific meaning. Calling A/C blind validation would fail this repair.

## Results: the comparative answer

**Before (constructed defect).** Figure 3 shows that the model predicts the lengths. It can be seen that the B result is 359.1575 μm and the experiment gives 359 μm. The widths are 153.3601, 143.0406 and 129.0462 μm. The depths are 40.4693, 31.1203 and 22.0445 μm. These results show excellent model accuracy.

**After.** The fitted B length differs from its 359 μm target by 0.16 μm, but the transverse dimensions reveal a broader discrepancy. At B, the predicted width is 143.0 μm compared with 123.5 μm, whereas the predicted depth is 31.1 μm compared with 36 μm. The same wide and shallow tendency is larger at C: width is 129.0 μm compared with 106 μm, and depth is 22.0 μm compared with 29.6 μm. The length fit therefore does not establish agreement for the fusion envelope across these conditions.

**Evidence and reasoning.** The dossier comparison table supplies every value and the fitted B role. The reader recovers a pattern and its conflict with an unrestricted accuracy claim. Rounding makes selected anchors readable without changing evidence. Measured means, units and unfavorable differences remain. The result does not interpret expanded U as specimen standard deviation or establish a significance test. A complete manuscript still needs A and the remaining observations at their appropriate locations.

## Discussion: observation and inference

**Before (constructed defect).** It is important to note that the high-temperature material properties are very important. The model is physically valid because the computation converged and geometry agrees at A. Melt convection causes the remaining differences.

**After.** Small geometry differences at A and the fitted B length coexist with width and depth discrepancies at B and C. This combination limits the evidence for transferring the fixed coefficient across operating conditions. All model temperatures above the solidus also exceed the endpoints of both property tables, so the high-temperature continuation rules enter the entire modeled fusion region. Their influence must be interpreted as sensitivity to a constitutive assumption. The geometry comparisons and numerical consistency checks do not identify liquid properties or establish the cause of the residual discrepancy.

**Evidence and reasoning.** Dossier sections “Actual model, equations and conditions,” “Calibration” and “Six unique production runs and numerical adequacy” separate numerical evidence, closure and physical evidence. The after paragraph removes an empty importance statement and unsupported convection attribution, retaining a concrete dependency: solidus 1290 °C exceeds the cp and k endpoints 1093 °C and 982 °C. No effect magnitude is invented. A later mechanism paragraph can compare plausible explanations when actual diagnostics are supplied.

These local candidates need independent review against the current manuscript, citations and adjoining passages. They do not replace the complete forward-use assignment. The semantic regression script tests explicit annotations on constructed counterexamples; it does not score this prose.
