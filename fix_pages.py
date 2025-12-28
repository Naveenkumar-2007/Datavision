# Fix script for Overview and Dashboards pages
import re

# Fix Overview.tsx
with open('frontend/src/pages/Overview.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the AutonomousRenderer section and add null check
old_renderer = '''      {/* Autonomous Renderer */}
      <AutonomousRenderer
        layoutSpec={overviewData.layout_spec}
        visualPrimitives={overviewData.visual_primitives}
        colorPalette={overviewData.color_palette}
        narrativeElements={overviewData.narrative_elements}
        data={rawData}
        mode="overview"
        isDarkMode={isDark}
      />'''

new_renderer = '''      {/* Autonomous Renderer */}
      {overviewData && (
        <AutonomousRenderer
          layoutSpec={overviewData.layout_spec}
          visualPrimitives={overviewData.visual_primitives}
          colorPalette={overviewData.color_palette}
          narrativeElements={overviewData.narrative_elements}
          data={rawData}
          mode="overview"
          isDarkMode={isDark}
        />
      )}'''

content = content.replace(old_renderer, new_renderer)

with open('frontend/src/pages/Overview.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed Overview.tsx - added null check for overviewData")

# Fix Dashboards.tsx  
with open('frontend/src/pages/Dashboards.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_d_renderer = '''      {/* Autonomous Renderer */}
      <AutonomousRenderer
        layoutSpec={dashboardData.layout_spec}
        visualPrimitives={dashboardData.visual_primitives}
        colorPalette={dashboardData.color_palette}
        narrativeElements={dashboardData.narrative_elements || []}
        data={rawData}
        mode="dashboard"
        isDarkMode={isDark}
      />'''

new_d_renderer = '''      {/* Autonomous Renderer */}
      {dashboardData && (
        <AutonomousRenderer
          layoutSpec={dashboardData.layout_spec}
          visualPrimitives={dashboardData.visual_primitives}
          colorPalette={dashboardData.color_palette}
          narrativeElements={dashboardData.narrative_elements || []}
          data={rawData}
          mode="dashboard"
          isDarkMode={isDark}
        />
      )}'''

content = content.replace(old_d_renderer, new_d_renderer)

with open('frontend/src/pages/Dashboards.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed Dashboards.tsx - added null check for dashboardData")
print("\n🎯 Pages should now load without crashing!")
print("📝 Please refresh browser with Ctrl+Shift+R (hard refresh)")
