# Keyboard Navigation Accessibility Audit
**Date:** 2025-12-19
**Auditor:** Claude (AgentHR)
**Scope:** All keyboard shortcuts documented in KeyboardShortcutsHelp component

## Executive Summary

This audit reviews all keyboard shortcuts documented in the AgentHR application for potential conflicts with browser and screen reader shortcuts, accessibility compliance, and implementation quality.

**Overall Status:** ⚠️ **NEEDS ATTENTION**

### Key Findings
- ✅ **18 total shortcuts** documented across 6 categories
- ⚠️ **3 critical conflicts** with browser shortcuts
- ⚠️ **2 potential conflicts** with screen reader shortcuts
- ✅ Good use of semantic keys (Escape, Enter, Arrow keys)
- ⚠️ Missing ARIA labels for some shortcuts
- ⚠️ Platform inconsistency (Ctrl vs Cmd for macOS)

---

## 1. Documented Shortcuts Inventory

### 1.1 Global Shortcuts (3 shortcuts)
| ID | Keys | Description | Conflict Risk |
|---|---|---|---|
| `global.search` | `Ctrl+K` | Open global search | ⚠️ Medium |
| `global.showShortcuts` | `Ctrl+/` | Show keyboard shortcuts help | ✅ Low |
| `global.closeModal` | `Escape` | Close modal or dialog | ✅ None |

### 1.2 Upload Shortcuts (2 shortcuts)
| ID | Keys | Description | Conflict Risk |
|---|---|---|---|
| `upload.focusZone` | `Ctrl+U` | Focus upload zone | ⚠️ High |
| `upload.cancel` | `Escape` | Cancel upload | ✅ None |

### 1.3 Vacancy Shortcuts (3 shortcuts)
| ID | Keys | Description | Conflict Risk |
|---|---|---|---|
| `vacancy.new` | `Ctrl+N` | Create new vacancy | 🔴 **CRITICAL** |
| `vacancy.search` | `Ctrl+F` | Focus search field | 🔴 **CRITICAL** |
| `vacancy.edit` | `Enter` | Edit selected vacancy | ✅ None |

### 1.4 Candidate Shortcuts (4 shortcuts)
| ID | Keys | Description | Conflict Risk |
|---|---|---|---|
| `candidate.openDetails` | `Enter` | Open candidate details | ✅ None |
| `candidate.closeDetails` | `Escape` | Close candidate details | ✅ None |
| `candidate.nextStage` | `Ctrl+→` | Move to next stage | ⚠️ Medium |
| `candidate.prevStage` | `Ctrl+←` | Move to previous stage | ⚠️ Medium |

### 1.5 Navigation Shortcuts (4 shortcuts)
| ID | Keys | Description | Conflict Risk |
|---|---|---|---|
| `nav.next` | `Arrow Down` or `→` | Next item/card | ✅ None |
| `nav.previous` | `Arrow Up` or `←` | Previous item/card | ✅ None |
| `nav.first` | `Home` | First item in list | ✅ None |
| `nav.last` | `End` | Last item in list | ✅ None |

### 1.6 Form Shortcuts (4 shortcuts)
| ID | Keys | Description | Conflict Risk |
|---|---|---|---|
| `form.save` | `Ctrl+S` | Save form | 🔴 **CRITICAL** |
| `form.nextField` | `Tab` | Next field | ✅ None (native) |
| `form.prevField` | `Shift+Tab` | Previous field | ✅ None (native) |
| `form.submit` | `Ctrl+Enter` | Submit form | ⚠️ Medium |

---

## 2. Browser Shortcut Conflicts

### 2.1 Critical Conflicts 🔴

#### `Ctrl+N` - Create new vacancy
**Browser Conflict:**
- **Chrome/Edge:** Opens new browser window
- **Firefox:** Opens new browser window
- **Safari:** Opens new browser window

**Impact:** HIGH - Users cannot open new browser windows when on vacancy pages

**Recommendation:**
- Change to `Alt+N` or provide a user setting to customize
- Add documentation that browser shortcut is overridden on this page
- Alternative: Use `Ctrl+Shift+N` (less common)

#### `Ctrl+F` - Focus search field
**Browser Conflict:**
- **All browsers:** Opens browser's "Find in Page" dialog

**Impact:** HIGH - Users lose access to browser's find functionality

**Recommendation:**
- Change to `Alt+F` or `/` (single key)
- Provide visual indicator when focus is in search field
- Keep browser's find functionality accessible

#### `Ctrl+S` - Save form
**Browser Conflict:**
- **All browsers:** Opens "Save As" dialog to save current page

**Impact:** MEDIUM - Users cannot save web pages as HTML

**Recommendation:**
- Keep this shortcut (common pattern for web apps)
- Add notification/toast when triggered to inform user
- Ensure users can still save page via menu if needed

### 2.2 Medium Risk Conflicts ⚠️

#### `Ctrl+K` - Open global search
**Browser Conflict:**
- **Chrome:** Opens "Search and browse the web" omnibox
- **Edge:** Opens search bar
- **Firefox:** Focuses search bar (if enabled)

**Impact:** MEDIUM - Overrides convenient browser search

**Recommendation:**
- Keep this (common web app pattern)
- Add tooltip/hint: "Press Ctrl+K for app search"

#### `Ctrl+U` - Focus upload zone
**Browser Conflict:**
- **All browsers:** Opens page source (View Source)

**Impact:** MEDIUM - Developers lose access to view source

**Recommendation:**
- Change to `Alt+U` or `Ctrl+Shift+U`
- Move this shortcut to a less prominent combination

#### `Ctrl+Enter` - Submit form
**Browser Conflict:**
- **Some browsers:** May have platform-specific behavior

**Impact:** LOW - Not a standardized browser shortcut

**Recommendation:**
- Keep this shortcut (common pattern)
- Document in form help text

---

## 3. Screen Reader Conflicts

### 3.1 NVDA (Windows) Conflicts

#### Potential Conflicts:
| Shortcut | NVDA Function | Impact |
|---|---|---|
| `Ctrl+Alt+K` | None (safe) | ✅ No conflict |
| `Ctrl+K` | None in NVDA | ✅ Safe |
| `Ctrl+F` | None (uses browser find) | ⚠️ May interfere |
| `Ctrl+S` | None | ✅ Safe |
| `Escape` | Stops speech | ✅ Appropriate behavior |
| `Arrow Keys` | Navigate/read content | ⚠️ Custom navigation may interfere |

**NVDA-Specific Concerns:**
1. **Arrow key navigation**: NVDA uses arrow keys to read content. Custom navigation with arrow keys may conflict.
   - **Recommendation:** Only activate custom arrow navigation when focus is in specific containers (kanban, lists). Add `role="application"` or manage focus carefully.

2. **Enter key**: NVDA uses Enter to activate links/buttons.
   - **Status:** ✅ Appropriate - the app's behavior aligns with screen reader expectations.

3. **Space key**: Not currently used but documented in code.
   - **Recommendation:** Avoid using Space as it toggles checkboxes and buttons in screen readers.

### 3.2 JAWS (Windows) Conflicts

#### Potential Conflicts:
| Shortcut | JAWS Function | Impact |
|---|---|---|
| `Ctrl+Shift+K` | List of links | ✅ No conflict |
| `Ctrl+K` | None in JAWS | ✅ Safe |
| `Ctrl+F` | None (uses browser) | ⚠️ May interfere |
| `Ctrl+S` | None | ✅ Safe |
| `Insert+Ctrl+Home` | Jump to top | ⚠️ Similar to `Home` shortcut |

**JAWS-Specific Concerns:**
1. **Insert key combinations**: JAWS heavily uses the Insert key (default JAWS key).
   - **Status:** ✅ No conflicts with documented shortcuts.

2. **Navigation quick keys**: JAWS uses single letters (N for next link, H for heading, etc.).
   - **Status:** ✅ No conflicts with documented shortcuts.

### 3.3 VoiceOver (macOS) Conflicts

#### Platform Difference:
- **Documented shortcuts use Ctrl**, but macOS uses Cmd (⌘) key
- **Code has platform detection** in `keyboardShortcuts.ts` ✅

**VoiceOver-Specific Concerns:**
1. **VO+Arrow keys**: VoiceOver uses VO+Arrow keys for navigation.
   - **Status:** ⚠️ Custom arrow key navigation may conflict.
   - **Recommendation:** Ensure VoiceOver users can disable custom navigation or use standard tab navigation.

2. **VO+Space**: VoiceOver activation.
   - **Status:** ✅ No conflict - app uses Enter for activation.

---

## 4. Accessibility Compliance Review

### 4.1 WCAG 2.1 Level AA Compliance

#### ✅ Compliant Areas:
1. **Keyboard Focusable**: All interactive elements appear to be keyboard accessible
2. **No Keyboard Trap**: Escape key is wired to close modals ✅
3. **Focus Order**: Tab/Shift+Tab navigation is standard ✅
4. **Semantic Keys**: Use of Enter, Escape, Arrow keys follows conventions ✅

#### ⚠️ Areas of Concern:
1. **Visible Focus Indicator**: Need to verify all interactive elements have visible focus states
2. **Skip Links**: No evidence of skip links for main content
3. **ARIA Labels**: Some shortcuts may lack ARIA labels
4. **Screen Reader Announcements**: No evidence that shortcut actions are announced to screen readers

### 4.2 Implementation Quality

#### Strengths:
✅ Well-documented shortcuts in `KeyboardShortcutsHelp.tsx`
✅ Centralized registry with priority-based conflict resolution
✅ Platform-aware key mapping (Mac vs Windows)
✅ Proper event cleanup in hooks
✅ Type-safe implementation with TypeScript
✅ Good use of `preventDefault` to stop unwanted browser behavior

#### Weaknesses:
⚠️ Missing ARIA live regions for shortcut feedback
⚠️ No visual indicators when shortcuts are available
⚠️ No user preference to disable/shortcuts
⚠️ Incomplete implementation (some shortcuts documented but not implemented)
⚠️ Missing focus management after shortcut actions
⚠️ No timeout/debounce for rapid key presses

---

## 5. Detailed Findings by Category

### 5.1 Critical Issues (Must Fix)

1. **Ctrl+N Overrides New Window**
   - **Impact:** Users cannot open new browser windows
   - **Fix:** Change to `Alt+N` or `Ctrl+Shift+N`

2. **Ctrl+F Overrides Find in Page**
   - **Impact:** Users lose browser find functionality
   - **Fix:** Change to `/` or `Alt+F`

3. **No Screen Reader Announcements**
   - **Impact:** Screen reader users don't know when shortcuts trigger actions
   - **Fix:** Add ARIA live regions and announcements

### 5.2 Important Issues (Should Fix)

1. **Platform Inconsistency**
   - macOS users see "Ctrl" but should see "Cmd" (⌘)
   - **Status:** Code has support but may not be fully implemented in UI
   - **Fix:** Ensure all UI displays use platform-aware formatting

2. **Arrow Key Navigation Conflicts**
   - May conflict with screen reader reading
   - **Fix:** Only activate in specific containers with `role="application"`

3. **Missing Focus Management**
   - After some shortcut actions, focus may be unclear
   - **Fix:** Ensure focus moves to appropriate element after each action

### 5.3 Minor Issues (Nice to Have)

1. **Visual Shortcut Hints**: No visible hints on buttons showing available shortcuts
2. **Customization**: No way for users to remap shortcuts
3. **Help Dialog Accessibility**: The help dialog itself should be fully accessible
4. **Shortcut Conflicts Dialog**: No warning when shortcuts conflict with browser

---

## 6. Recommendations

### 6.1 Immediate Actions (Priority 1)

1. **Change Critical Shortcuts:**
   ```typescript
   // CHANGE: Ctrl+N → Alt+N
   { id: 'vacancy.new', keys: ['Alt', 'N'], ... }

   // CHANGE: Ctrl+F → / (forward slash)
   { id: 'vacancy.search', keys: ['/'], ... }

   // KEEP: Ctrl+S (common web app pattern)
   // Add toast notification when triggered
   ```

2. **Add ARIA Live Regions:**
   ```tsx
   <div role="status" aria-live="polite" aria-atomic="true">
     {shortcutFeedback}
   </div>
   ```

3. **Fix Platform Display:**
   - Ensure macOS users see "⌘" instead of "Ctrl"
   - Update KeyboardShortcutsHelp to use platform-aware rendering

### 6.2 Short-term Improvements (Priority 2)

1. **Add Screen Reader Testing:**
   - Test all shortcuts with NVDA on Windows
   - Test all shortcuts with VoiceOver on macOS
   - Document screen reader-specific behaviors

2. **Improve Focus Management:**
   ```typescript
   const handleShortcut = (action: () => void, focusTarget?: HTMLElement) => {
     action();
     focusTarget?.focus();
     announceToScreenReader(actionDescription);
   };
   ```

3. **Add Visual Indicators:**
   - Show keyboard shortcuts in tooltips
   - Add shortcut hints to common buttons

### 6.3 Long-term Enhancements (Priority 3)

1. **User Preferences:**
   - Allow users to customize shortcuts
   - Allow users to disable specific shortcuts
   - Remember preferences in localStorage

2. **Shortcut Conflict Detection:**
   - Warn users when shortcuts conflict with browser
   - Provide alternative suggestions

3. **Comprehensive Testing:**
   - Automated tests for keyboard navigation
   - Screen reader testing in CI/CD
   - Regular accessibility audits

---

## 7. Testing Checklist

### Manual Verification Required

- [ ] Test all 18 shortcuts in Chrome, Firefox, Safari, Edge
- [ ] Test with NVDA (Windows) - verify no conflicts
- [ ] Test with JAWS (Windows) - verify no conflicts
- [ ] Test with VoiceOver (macOS) - verify Cmd key works
- [ ] Verify Tab navigation works normally
- [ ] Verify Escape closes all modals/dialogs
- [ ] Verify focus is visible on all interactive elements
- [ ] Verify focus moves appropriately after each shortcut action
- [ ] Test with keyboard only (no mouse)
- [ ] Test with screen reader announcement on all shortcut actions

### Screen Reader Testing Steps

**NVDA (Windows):**
1. Enable NVDA
2. Navigate to application
3. Test each shortcut:
   - Press shortcut
   - Verify NVDA announces the action
   - Verify focus moves to expected location
   - Verify no NVDA shortcuts are blocked

**VoiceOver (macOS):**
1. Enable VoiceOver (Cmd+F5)
2. Navigate to application
3. Test each Cmd+⌘ shortcut:
   - Press Cmd+K (should be ⌘+K in UI)
   - Verify VoiceOver announces the action
   - Verify VO+Arrow keys still work for reading
   - Verify focus is managed correctly

---

## 8. Conclusion

The keyboard navigation implementation in AgentHR is **well-structured and thoughtful** but has **critical conflicts** that must be addressed for full accessibility compliance.

### Overall Assessment: **⚠️ CONDITIONAL PASS**

**Strengths:**
- Good architecture with centralized registry
- Comprehensive documentation
- Platform-aware implementation
- Standard patterns (Escape, Enter, Tab)

**Critical Issues:**
- Ctrl+N, Ctrl+F conflict with essential browser functions
- Missing screen reader announcements
- Platform display inconsistencies

**Next Steps:**
1. Fix critical shortcut conflicts (Ctrl+N, Ctrl+F)
2. Add screen reader announcements with ARIA live regions
3. Test with real screen readers (NVDA, JAWS, VoiceOver)
4. Document screen reader-specific behaviors
5. Consider user customization options

---

## Appendix A: Keyboard Shortcuts Reference

### Full List of Documented Shortcuts (18 total)

```
GLOBAL (3)
  Ctrl+K     - Open global search
  Ctrl+/     - Show keyboard shortcuts help
  Escape     - Close modal or dialog

UPLOAD (2)
  Ctrl+U     - Focus upload zone
  Escape     - Cancel upload

VACANCY (3)
  Ctrl+N     - Create new vacancy [CONFLICT]
  Ctrl+F     - Focus search field [CONFLICT]
  Enter      - Edit selected vacancy

CANDIDATE (4)
  Enter      - Open candidate details
  Escape     - Close candidate details
  Ctrl+→     - Move to next stage
  Ctrl+←     - Move to previous stage

NAVIGATION (4)
  Arrow Down/→ - Next item/card
  Arrow Up/←   - Previous item/card
  Home         - First item in list
  End          - Last item in list

FORMS (4)
  Ctrl+S     - Save form [CONFLICT]
  Tab        - Next field
  Shift+Tab  - Previous field
  Ctrl+Enter - Submit form
```

---

## Appendix B: Browser Shortcut Reference

### Common Browser Shortcuts (Do Not Override)

**CRITICAL - Never Override:**
- `Ctrl+T` - New tab
- `Ctrl+W` - Close tab
- `Ctrl+R` - Reload
- `Ctrl+Shift+R` - Hard reload
- `F12` - Developer Tools
- `F11` - Fullscreen
- `Ctrl+Shift+N` - Incognito/Private window
- `Ctrl+Shift+T` - Reopen closed tab
- `Ctrl+L` - Focus address bar
- `Ctrl+D` - Bookmark page

**HIGH RISK - Avoid Overriding:**
- `Ctrl+N` - New window ⚠️
- `Ctrl+F` - Find in page ⚠️
- `Ctrl+P` - Print
- `Ctrl+S` - Save page ⚠️
- `Ctrl+C` - Copy
- `Ctrl+V` - Paste
- `Ctrl+X` - Cut
- `Ctrl+Z` - Undo
- `Ctrl+Y` - Redo
- `Ctrl+A` - Select all

**MEDIUM RISK - Use with Caution:**
- `Ctrl+K` - Search bar (Chrome) ⚠️
- `Ctrl+U` - View source ⚠️
- `Ctrl+H` - History
- `Ctrl+J` - Downloads

**SAFE - Commonly Overridden in Web Apps:**
- `Ctrl+/` - Shortcuts help ✅
- `Ctrl+Enter` - Submit form ✅
- `Ctrl+Space` - Open menu ✅
- `Escape` - Close/dismiss ✅
- `Arrow keys` - Custom navigation ✅ (with care)
- `Home/End` - Jump to start/end ✅

---

**End of Audit Report**
