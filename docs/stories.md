
# Odyssey HMI: Mission Scenarios

This document outlines the three core, pre-scripted scenarios that the Odyssey HMI simulator can run. These stories define the operator's role, their expected actions, and the system's behavior. They also detail the events that will be captured in the Mission Log for post-mission analysis.

---

### Scenario 1: The Nominal Mission (The "Happy Path")

*   **Goal:** Demonstrate the HMI's ability to provide clear situational awareness and handle routine operator commands during a successful, uneventful mission.
*   **The Story:**
    1.  The Odyssey ROV begins its automated descent (`en_route`).
    2.  Upon reaching 2000m, the mission status changes to `searching`.
    3.  After 30 seconds, an informational alert appears: `"INFO: Bioluminescent signature detected. Ready to deploy manipulator arm."`
    4.  The operator follows the prompt to deploy the arm and collect the sample.
    5.  Once collected, the mission status changes to `returning`, and the ROV ascends, concluding in `mission_success`.
*   **Operator's Actions:**
    *   Observe the descent and the transition to searching.
    *   When prompted by the INFO alert, use the `SubsystemControls` to click **"Deploy Arm"**.
    *   Once the arm is deployed, click **"Collect Sample"**.
    *   Observe the successful return.
*   **Resulting Mission Log (viewable via gRPC):**
    *   `[INFO] Scenario Started: Nominal Mission.`
    *   `[INFO] Mission status changed to 'en_route'.`
    *   `[INFO] Mission status changed to 'searching'.`
    *   `[INFO] Bioluminescent signature detected. Awaiting operator action.`
    *   `[OPERATOR] Command Sent: DEPLOY_ARM.`
    *   `[INFO] Manipulator arm status changed to 'deployed'.`
    *   `[OPERATOR] Command Sent: COLLECT_SAMPLE.`
    *   `[INFO] Sample collected successfully.`
    *   `[INFO] Mission status changed to 'returning'.`
    *   `[INFO] Mission status changed to 'mission_success'.`

---

### Scenario 2: The Pressure Anomaly (Warning & Escalation)

*   **Goal:** Test the HMI's alerting for a `WARNING` state, the operator's response, and the system's escalation to `CRITICAL` if no action is taken.
*   **The Story:** During descent, the ROV's hull pressure enters a `WARNING` state. The HMI displays yellow alerts and advises the operator to halt the descent.
    *   **Path A (Successful Intervention):** The operator issues an "All Stop" command. The descent halts, pressure normalizes, the alert clears, and the mission continues.
    *   **Path B (Operator Inaction & Failure):** If the operator does not act within 30 seconds, the pressure escalates to a `CRITICAL` state. If another 15 seconds pass with no action, the mission ends in `mission_failure_hull_breach`.
*   **Operator's Actions:**
    *   **Path A:** Respond to the `WARNING` by clicking the **"All Stop"** button in the Propulsion card.
    *   **Path B:** Take no action and observe the escalation and subsequent failure.
*   **Resulting Mission Log (Path A - Success):**
    *   `[INFO] Scenario Started: Pressure Anomaly.`
    *   `[INFO] Mission status changed to 'en_route'.`
    *   `[WARNING] Hull pressure exceeds nominal limits.`
    *   `[OPERATOR] Command Sent: SET_PROPULSION_STATE(inactive).`
    *   `[INFO] Hull pressure returned to nominal.`
*   **Resulting Mission Log (Path B - Failure):**
    *   `[INFO] Scenario Started: Pressure Anomaly.`
    *   `[INFO] Mission status changed to 'en_route'.`
    *   `[WARNING] Hull pressure exceeds nominal limits.`
    *   `[CRITICAL] Hull pressure has reached a critical level!`
    *   `[CRITICAL] Mission status changed to 'mission_failure_hull_breach'.`

---

### Scenario 3: The Critical Power Fault (Emergency & Consequence)

*   **Goal:** Test a sudden `CRITICAL` alert and the operator's use of a guarded, irreversible command, demonstrating the consequence of inaction.
*   **The Story:** While `searching` at depth, a power fault occurs, causing a catastrophic battery drain. The HMI flashes red alerts, instructing the operator to jettison the science package to save the ROV.
    *   **Path A (Successful Intervention):** The operator uses the "Jettison Package" guarded button. The package is dropped, the power drain stabilizes, and the ROV begins an `emergency_ascent`. The vehicle is saved.
    *   **Path B (Operator Inaction & Failure):** If the operator does not act, the battery drains to 0% within 60 seconds. The HMI goes dark, telemetry ceases, and the mission ends in `mission_failure_lost_signal`. The ROV is lost.
*   **Operator's Actions:**
    *   **Path A:** Respond to the `CRITICAL` alert by activating the guarded **"Jettison Package"** command and confirming the action.
    *   **Path B:** Take no action and observe the rapid battery depletion and loss of signal.
*   **Resulting Mission Log (Path A - Success):**
    *   `[INFO] Scenario Started: Critical Power Fault.`
    *   `[INFO] Mission status changed to 'searching'.`
    *   `[CRITICAL] Power system fault detected. Catastrophic battery drain.`
    *   `[OPERATOR] Command Sent: JETTISON_PACKAGE.`
    *   `[INFO] Science package jettisoned. Power drain stabilized.`
    *   `[INFO] Mission status changed to 'emergency_ascent'.`
*   **Resulting Mission Log (Path B - Failure):**
    *   `[INFO] Scenario Started: Critical Power Fault.`
    *   `[INFO] Mission status changed to 'searching'.`
    *   `[CRITICAL] Power system fault detected. Catastrophic battery drain.`
    *   `[CRITICAL] Battery at 0%. Signal lost.`
    *   `[CRITICAL] Mission status changed to 'mission_failure_lost_signal'.`

