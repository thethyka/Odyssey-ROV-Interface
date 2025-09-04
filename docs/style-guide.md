# The "How"

## Design Philosophy

Based on our philosophy, our style guide is going to include mainly greyscale colours, and a few colours for state. As most ROV operation rooms are dimly lit to reduce eye strain, the control panel will be coloured accordingly. 

## Color Palette

The palette will dark and cool, and the state colours will be bright to stand out.

### Primary Palette

Used for the main interface structure, text, and non-interactive elements.

| Swatch | Name | Hex Code | Usage |
| :--- | :--- | :--- | :--- |
| <div style="width:15px;height:15px;background:#111827"></div> | `background` | `#111827` | The base color for the entire application background. |
| <div style="width:15px;height:15px;background:#1F2937"></div> | `surface` | `#1F2937` | Background for individual components, cards, and modal windows. |
| <div style="width:15px;height:15px;background:#F3F4F6;border:1px solid #ccc"></div> | `text-primary` | `#F3F4F6` | Primary text, titles, and important labels. |
| <div style="width:15px;height:15px;background:#9CA3AF"></div> | `text-secondary` | `#9CA3AF` | Secondary information, annotations, and disabled element text. |
| <div style="width:15px;height:15px;background:#374151"></div> | `border` | `#374151` | Borders for components, panels, and interactive elements. |



### State & Accent Palette

Used exclusively to convey system status, alerts, or provide interactive feedback. **Never use these colors for decoration.**

| Swatch | Name | Hex Code | Usage |
| :--- | :--- | :--- | :--- |
| <div style="width:15px;height:15px;background:#F87171"></div> | `critical` | `#F87171` | Alarms, critical faults, danger states (e.g., Hull Breach). |
| <div style="width:15px;height:15px;background:#FBBF24"></div> | `warning` | `#FBBF24` | Warnings, abnormal conditions, caution states (e.g., Low Battery). |
| <div style="width:15px;height:15px;background:#34D399"></div> | `nominal` | `#34D399` | Indicates an active, positive, or successful state (e.g., System Online, Sample Collected). Use sparingly; `text-primary` or `text-secondary` often represents a normal idle state. |
| <div style="width:15px;height:15px;background:#60A5FA"></div> | `info` | `#60A5FA` | Interactive feedback (hover, active), selected items, or purely informational messages. |

## 3. Typography

Typography must be exceptionally clear and legible on-screen in a variety of sizes. We use two primary font families.

-   **Primary Font:** **Inter**
    -   Sans-serif, readable
    -   *Source:* [Google Fonts - Inter](https://fonts.google.com/specimen/Inter)
-   **Data Font:** **Source Code Pro**
    -   Monospaced
    -   *Source:* [Google Fonts - Source Code Pro](https://fonts.google.com/specimen/Source+Code+Pro)

### Typographic Scale

-   **Heading 1 (`<h1>`):** `Inter Bold` - 24px - `text-primary`
-   **Heading 2 (`<h2>`):** `Inter SemiBold` - 18px - `text-primary`
-   **Body Text (`<p>`):** `Inter Regular` - 14px - `text-secondary`
-   **UI Label:** `Inter Medium` - 12px - `text-secondary` (UPPERCASE)
-   **Data Readout:** `Source Code Pro Regular` - 16px - `text-primary`

---

## 4. Iconography

Icons must be simple, unambiguous, and instantly recognizable. They should feel like precise technical symbols.

-   **Library:** **Phosphor Icons**
    -   Provides a vast, consistent, and clean set of icons perfect for technical interfaces.
    -   *Source:* [phosphoricons.com](https://phosphoricons.com/)
-   **Style:**
    -   Use the **"thin"** or **"light"** weight.
    -   Icons should be `24px` x `24px` for clarity.
    -   Default color is `text-secondary`. Use `info`, `warning`, etc., for status icons.

### Examples

| Icon | Name | Usage |
| :--- | :--- | :--- |
|<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#FFFFFF" viewBox="0 0 256 256"><path d="M150.81,131.79a8,8,0,0,1,.35,7.79l-16,32a8,8,0,0,1-14.32-7.16L131.06,144H112a8,8,0,0,1-7.16-11.58l16-32a8,8,0,1,1,14.32,7.16L124.94,128H144A8,8,0,0,1,150.81,131.79ZM96,16h64a8,8,0,0,0,0-16H96a8,8,0,0,0,0,16ZM200,56V224a24,24,0,0,1-24,24H80a24,24,0,0,1-24-24V56A24,24,0,0,1,80,32h96A24,24,0,0,1,200,56Zm-16,0a8,8,0,0,0-8-8H80a8,8,0,0,0-8,8V224a8,8,0,0,0,8,8h96a8,8,0,0,0,8-8Z"></path></svg> | Battery Charging | Battery charge status. |
|<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#FFFFFF" viewBox="0 0 256 256"><path d="M207.06,72.67A111.24,111.24,0,0,0,128,40h-.4C66.07,40.21,16,91,16,153.13V176a16,16,0,0,0,16,16H224a16,16,0,0,0,16-16V152A111.25,111.25,0,0,0,207.06,72.67ZM224,176H119.71l54.76-75.3a8,8,0,0,0-12.94-9.42L99.92,176H32V153.13c0-3.08.15-6.12.43-9.13H56a8,8,0,0,0,0-16H35.27c10.32-38.86,44-68.24,84.73-71.66V80a8,8,0,0,0,16,0V56.33A96.14,96.14,0,0,1,221,128H200a8,8,0,0,0,0,16h23.67c.21,2.65.33,5.31.33,8Z"></path></svg> | Gauge | Pressure or thruster output. |
|<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#FFFFFF" viewBox="0 0 256 256"><path d="M248,200h-8a8,8,0,0,1-8-8V160a8,8,0,0,1,8-8h8a8,8,0,0,0,0-16h-8a24,24,0,0,0-24,24v8H199.2a40.09,40.09,0,0,0-33.71-31.61L129.44,49.85A16,16,0,0,0,114.67,40H24A16,16,0,0,0,8,56v96a40,40,0,0,0,32,64H160a40.07,40.07,0,0,0,39.2-32H216v8a24,24,0,0,0,24,24h8a8,8,0,0,0,0-16ZM148,136H64V56h50.67ZM48,56v80H40a39.72,39.72,0,0,0-16,3.35V56ZM160,200H40a24,24,0,0,1,0-48H160a24,24,0,0,1,0,48Zm8-24a8,8,0,0,1-8,8H40a8,8,0,0,1,0-16H160A8,8,0,0,1,168,176Z"></path></svg>| Manipulator Arm | Robotic arm subsystem. |
|<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#FFFFFF" viewBox="0 0 256 256"><path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm-8-80V80a8,8,0,0,1,16,0v56a8,8,0,0,1-16,0Zm20,36a12,12,0,1,1-12-12A12,12,0,0,1,140,172Z"></path></svg>| Warning | A general warning indicator. |

---

## 5. Component States

### Indicators & Data Displays

-   **Standard Readout:**
    -   A `UI Label` in `text-secondary` above a `Data Readout` in `text-primary`.
    -   `THRUSTER OUTPUT`
    -   `85.2%`

-   **Stateful Readout:**
    -   When a value enters a non-nominal state, the `Data Readout` text changes to the corresponding state color.
    -   `BATTERY LEVEL`
    -   <span style="color:#FBBF24;">15.5%</span> (Warning State)
