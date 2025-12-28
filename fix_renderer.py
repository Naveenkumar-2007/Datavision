# Fix script for AutonomousRenderer.tsx
import re

# Read file
with open('frontend/src/components/AutonomousRenderer.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add correlation_map mapping (insert after relationship_mapper line)
content = content.replace(
    "        case 'relationship_mapper':",
    "        case 'correlation_map':  // NEW: Handle correlation_map from V2 engines\n        case 'relationship_mapper':"
)

# Add density_surface mapping (insert after distribution_surface line)  
content = content.replace(
    "        case 'distribution_surface':",
    "        case 'density_surface':  // NEW: Handle density_surface from V2 engines\n        case 'distribution_surface':"
)

# Write back
with open('frontend/src/components/AutonomousRenderer.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed! Added mappings for:")
print("   - correlation_map → relationship_mapper (scatter chart)")
print("   - density_surface → distribution_surface (histogram)")
