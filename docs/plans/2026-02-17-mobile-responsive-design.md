# Mobile Responsive Design Plan

## Goal
Refactor the current `NeoDashboard` desktop-centric layout to be fully responsive on mobile devices without compromising the desktop experience.

## Design Strategy: Mobile-First

### 1. Main Layout (`NeoDashboard.tsx`)
- **Current**: Fixed `grid-cols-12` height `100vh`.
- **New**:
    - **Mobile**: `flex flex-col` (Vertical Stack), Auto height.
    - **Desktop (`lg` breakpoint)**: `grid grid-cols-12`, fixed `h-screen`.

### 2. Component Adaptation
| Component | Mobile View | Desktop View |
|-----------|-------------|--------------|
| **FocusMetrics** | Top/First. Full width. Collapsible or compacted? | Left Column (Col-4). Full Height. |
| **Main Chart** | Middle. Fixed height (e.g., 350px). | Center Column (Col-5). Full Height. |
| **MarketOverview** | Bottom. Fixed height (e.g., 400px) or flex-grow. | Right Column (Col-3). Full Height. |
| **ProTicker** | **Hidden** (Too sparse on small screens). | Bottom Fixed. |
| **Header** | Compact (Hide "System Online" badge). | Full Info. |
| **Timeframe Selector** | Horizontal Scroll or Grid (2 rows). | Flex Row. |

### 3. Detailed Changes

#### A. `NeoDashboard.tsx`
```tsx
<div className="flex flex-col lg:grid lg:h-screen lg:grid-cols-12 ...">
    {/* Focus Metrics */}
    <div className="order-2 w-full lg:order-1 lg:col-span-4 lg:h-full ...">
       <FocusMetrics />
    </div>

    {/* Chart Area */}
    <div className="order-1 h-[400px] w-full lg:order-2 lg:col-span-5 lg:h-full ...">
       <StockChart />
       <TimeframeButtons className="overflow-x-auto whitespace-nowrap" />
    </div>

    {/* Market Overview */}
    <div className="order-3 h-[400px] w-full lg:order-3 lg:col-span-3 lg:h-full ...">
       <MarketOverview />
    </div>
</div>
```
*Note: On mobile, users usually want to see the Chart first (Order 1), then Metrics (Order 2), then List (Order 3).*

#### B. `FocusMetrics.tsx`
- Remove `h-full` constraint on mobile.
- Allow content to flow naturally.
- Reduce font sizes for `text-6xl` price to `text-4xl` on mobile.

#### C. `StockChart.tsx`
- Ensure wrapper handles dynamic height correctly.

### 4. Implementation Steps
1.  **Modify `NeoDashboard.tsx`**: Apply `flex-col` / `lg:grid` classes. Reorder elements for mobile logic.
2.  **Modify `FocusMetrics.tsx`**: Add responsive text sizes (`text-4xl md:text-6xl`).
3.  **Modify `ProTicker`**: Add `hidden lg:flex`.
4.  **Verify**: Check layout on mobile simulator and desktop.

## User Review Required
- **Order of Elements**: Chart first, then Metrics, then List on mobile?
- **Hiding Ticker**: Is it acceptable to hide the bottom ticker on mobile?
