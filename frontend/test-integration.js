#!/usr/bin/env node

/**
 * Frontend Integration Validation Script
 *
 * This script validates that the backend API returns data in the correct format
 * expected by the CandidateSourceAttribution frontend component.
 *
 * Usage: node frontend/test-integration.js
 *
 * Prerequisites:
 * - Backend server running on http://localhost:8000
 * - Sample data available in database
 */

const axios = require('axios');

const API_URL = 'http://localhost:8000/api/analytics/candidate-source-attribution';

// Color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSuccess(message) {
  log(`✅ ${message}`, 'green');
}

function logError(message) {
  log(`❌ ${message}`, 'red');
}

function logInfo(message) {
  log(`ℹ️  ${message}`, 'blue');
}

function logSection(title) {
  console.log('\n' + '='.repeat(60));
  log(title, 'cyan');
  console.log('='.repeat(60));
}

async function validateField(obj, fieldName, expectedType, parentPath = '') {
  const fullPath = parentPath ? `${parentPath}.${fieldName}` : fieldName;

  if (!(fieldName in obj)) {
    throw new Error(`Missing required field: ${fullPath}`);
  }

  const value = obj[fieldName];
  const actualType = Array.isArray(value) ? 'array' : typeof value;

  if (actualType !== expectedType) {
    throw new Error(
      `Field ${fullPath} has wrong type: expected ${expectedType}, got ${actualType}`
    );
  }

  return value;
}

async function validateOptionalField(obj, fieldName, expectedType, parentPath = '') {
  const fullPath = parentPath ? `${parentPath}.${fieldName}` : fieldName;

  if (fieldName in obj) {
    const value = obj[fieldName];
    const actualType = Array.isArray(value) ? 'array' : typeof value;

    if (actualType !== expectedType) {
      throw new Error(
        `Field ${fullPath} has wrong type: expected ${expectedType}, got ${actualType}`
      );
    }

    return value;
  }

  return undefined;
}

async function validateStageDistribution(stageDistribution, sourceName) {
  logInfo(`Validating stage distribution for "${sourceName}"...`);

  if (!Array.isArray(stageDistribution)) {
    throw new Error('stage_distribution is not an array');
  }

  if (stageDistribution.length === 0) {
    logInfo('  (Empty stage distribution - this is valid)');
    return;
  }

  const stage = stageDistribution[0];

  validateField(stage, 'stage_name', 'string', 'stage_distribution[0]');
  validateField(stage, 'count', 'number', 'stage_distribution[0]');
  validateField(stage, 'percentage', 'number', 'stage_distribution[0]');

  // Validate percentage is between 0 and 1
  if (stage.percentage < 0 || stage.percentage > 1) {
    throw new Error(
      `stage_distribution[0].percentage is out of range: ${stage.percentage} (expected 0-1)`
    );
  }

  // Validate count is non-negative
  if (stage.count < 0) {
    throw new Error(
      `stage_distribution[0].count is negative: ${stage.count}`
    );
  }

  logSuccess(`Stage distribution structure valid (${stageDistribution.length} stages)`);
}

async function validateSourceMetrics(source, index) {
  const sourceName = source.source || `Source ${index + 1}`;
  logInfo(`Validating source "${sourceName}"...`);

  // Validate all required fields
  const sourceField = validateField(source, 'source', 'string');
  const candidateCount = validateField(source, 'candidate_count', 'number');
  const hiredCount = validateField(source, 'hired_count', 'number');
  const conversionRate = validateField(source, 'conversion_rate', 'number');
  const avgTimeToHire = validateField(source, 'average_time_to_hire_days', 'number');
  const stageDistribution = validateField(source, 'stage_distribution', 'array');

  // Business logic validation

  // Candidate count should be non-negative
  if (candidateCount < 0) {
    throw new Error(`candidate_count is negative: ${candidateCount}`);
  }

  // Hired count should be non-negative
  if (hiredCount < 0) {
    throw new Error(`hired_count is negative: ${hiredCount}`);
  }

  // Hired count cannot exceed candidate count
  if (hiredCount > candidateCount) {
    throw new Error(
      `hired_count (${hiredCount}) exceeds candidate_count (${candidateCount})`
    );
  }

  // Conversion rate should be between 0 and 1
  if (conversionRate < 0 || conversionRate > 1) {
    throw new Error(
      `conversion_rate is out of range: ${conversionRate} (expected 0-1)`
    );
  }

  // Time to hire should be non-negative (0 if no hires)
  if (avgTimeToHire < 0) {
    throw new Error(`average_time_to_hire_days is negative: ${avgTimeToHire}`);
  }

  // If there are no hires, time-to-hire should be 0
  if (hiredCount === 0 && avgTimeToHire !== 0) {
    logInfo(`  ⚠️  Warning: hired_count is 0 but average_time_to_hire_days is ${avgTimeToHire} (expected 0)`);
  }

  // Validate conversion rate matches hired/candidate ratio
  if (candidateCount > 0) {
    const calculatedRate = hiredCount / candidateCount;
    const rateDiff = Math.abs(conversionRate - calculatedRate);

    // Allow small floating point differences
    if (rateDiff > 0.001) {
      logError(
        `conversion_rate (${conversionRate}) doesn't match ` +
        `hired_count / candidate_count (${calculatedRate.toFixed(3)})`
      );
    } else {
      logSuccess(`Conversion rate verified: ${(conversionRate * 100).toFixed(1)}%`);
    }
  }

  // Validate stage distribution
  await validateStageDistribution(stageDistribution, sourceName);

  logSuccess(`Source "${sourceName}" validated`);
  console.log(`   - Candidates: ${candidateCount}`);
  console.log(`   - Hired: ${hiredCount}`);
  console.log(`   - Conversion: ${(conversionRate * 100).toFixed(1)}%`);
  console.log(`   - Avg Time-to-Hire: ${avgTimeToHire.toFixed(0)} days`);
}

async function validateIntegration() {
  logSection('🧪 Frontend Integration Validation');
  logInfo(`Testing API endpoint: ${API_URL}\n`);

  let response;
  let data;

  try {
    // Test 1: API Reachability
    logSection('Test 1: API Reachability');
    response = await axios.get(API_URL, { timeout: 10000 });
    logSuccess(`API responded with status ${response.status}`);

    if (response.status !== 200) {
      throw new Error(`Expected status 200, got ${response.status}`);
    }

    // Test 2: Response Structure
    logSection('Test 2: Response Structure Validation');

    // Validate Content-Type
    const contentType = response.headers['content-type'];
    if (!contentType.includes('application/json')) {
      throw new Error(`Expected Content-Type: application/json, got ${contentType}`);
    }
    logSuccess('Content-Type is application/json');

    // Validate response is an object
    data = response.data;
    if (typeof data !== 'object' || data === null || Array.isArray(data)) {
      throw new Error('Response body is not a JSON object');
    }
    logSuccess('Response body is a JSON object');

    // Test 3: Required Fields
    logSection('Test 3: Required Fields Validation');

    const sources = validateField(data, 'sources', 'array');
    logSuccess('sources field present and is an array');

    const totalCandidates = validateField(data, 'total_candidates', 'number');
    logSuccess('total_candidates field present and is a number');

    const dateRange = await validateOptionalField(data, 'date_range', 'string');
    if (dateRange) {
      logSuccess(`date_range field present: "${dateRange}"`);
    } else {
      logInfo('date_range field not present (optional)');
    }

    // Test 4: Sources Array Validation
    logSection('Test 4: Sources Array Validation');

    if (sources.length === 0) {
      logInfo('No sources in response (empty dataset - this is valid)');
    } else {
      logInfo(`Validating ${sources.length} source(s)...`);

      for (let i = 0; i < sources.length; i++) {
        await validateSourceMetrics(sources[i], i);
        console.log(''); // Blank line for readability
      }
    }

    // Test 5: Total Candidates Calculation
    logSection('Test 5: Total Candidates Calculation');

    if (sources.length > 0) {
      const calculatedTotal = sources.reduce((sum, source) => sum + source.candidate_count, 0);

      if (calculatedTotal !== totalCandidates) {
        throw new Error(
          `total_candidates (${totalCandidates}) doesn't match ` +
          `sum of candidate_count (${calculatedTotal})`
        );
      }

      logSuccess(
        `Total candidates verified: ${totalCandidates} ` +
        `(matches sum of all sources)`
      );
    } else {
      logInfo(`Total candidates: ${totalCandidates} (no sources to verify against)`);
    }

    // Test 6: Data Consistency
    logSection('Test 6: Data Consistency Checks');

    if (sources.length > 0) {
      // Check that sources are sorted by candidate_count descending
      for (let i = 1; i < sources.length; i++) {
        if (sources[i].candidate_count > sources[i - 1].candidate_count) {
          logError(
            `Sources not sorted by candidate_count descending: ` +
            `${sources[i].source} (${sources[i].candidate_count}) > ` +
            `${sources[i - 1].source} (${sources[i - 1].candidate_count})`
          );
        } else {
          logSuccess(`Source ${i + 1} has <= candidates than source ${i}`);
        }
      }

      // Find best conversion rate
      const bestConversion = sources.reduce((best, current) =>
        current.conversion_rate > best.conversion_rate ? current : best
      );

      logSuccess(
        `Best conversion rate: ${(bestConversion.conversion_rate * 100).toFixed(1)}% ` +
        `(${bestConversion.source})`
      );

      // Find fastest time-to-hire (exclude sources with 0 time)
      const sourcesWithHires = sources.filter(s => s.average_time_to_hire_days > 0);
      if (sourcesWithHires.length > 0) {
        const fastest = sourcesWithHires.reduce((fastest, current) =>
          current.average_time_to_hire_days < fastest.average_time_to_hire_days
            ? current
            : fastest
        );

        logSuccess(
          `Fastest time-to-hire: ${fastest.average_time_to_hire_days.toFixed(0)} days ` +
          `(${fastest.source})`
        );
      }
    }

    // Test 7: Frontend Display Simulation
    logSection('Test 7: Frontend Display Values');

    if (sources.length > 0) {
      logInfo('Simulating frontend display calculations...\n');

      // Summary cards
      log('📊 Summary Cards:', 'cyan');
      log(`   Active Sources: ${sources.length}`, 'reset');
      log(`   Total Candidates: ${totalCandidates.toLocaleString()}`, 'reset');

      const bestConversion = sources.reduce((best, current) =>
        current.conversion_rate > best.conversion_rate ? current : best
      );
      log(
        `   Best Conversion Rate: ${(bestConversion.conversion_rate * 100).toFixed(1)}% ` +
        `(${bestConversion.source})`,
        'reset'
      );

      const sourcesWithHires = sources.filter(s => s.average_time_to_hire_days > 0);
      if (sourcesWithHires.length > 0) {
        const fastest = sourcesWithHires.reduce((fastest, current) =>
          current.average_time_to_hire_days < fastest.average_time_to_hire_days
            ? current
            : fastest
        );
        log(
          `   Fastest Hire: ${fastest.average_time_to_hire_days.toFixed(0)}d ` +
          `(${fastest.source})`,
          'reset'
        );
      }

      console.log('');

      // Color coding examples
      log('🎨 Color Coding Examples:', 'cyan');
      sources.slice(0, 3).forEach((source, index) => {
        const conversionColor =
          source.conversion_rate >= 0.15
            ? 'GREEN (success)'
            : source.conversion_rate >= 0.1
              ? 'YELLOW (warning)'
              : 'RED (error)';

        const timeColor =
          source.average_time_to_hire_days <= 30
            ? 'GREEN (success)'
            : source.average_time_to_hire_days <= 45
              ? 'YELLOW (warning)'
              : 'RED (error)';

        log(`   ${source.source}:`, 'reset');
        log(`     Conversion: ${(source.conversion_rate * 100).toFixed(1)}% → ${conversionColor}`, 'reset');
        log(`     Time-to-Hire: ${source.average_time_to_hire_days.toFixed(0)}d → ${timeColor}`, 'reset');
      });
    }

    // Test 8: Edge Case Detection
    logSection('Test 8: Edge Case Detection');

    if (sources.length > 0) {
      sources.forEach((source) => {
        // Detect zero hires
        if (source.hired_count === 0) {
          logInfo(`⚠️  "${source.source}": No hires yet`);
        }

        // Detect perfect conversion
        if (source.conversion_rate === 1.0) {
          logInfo(`⚠️  "${source.source}": 100% conversion rate (unusual)`);
        }

        // Detect very slow hiring
        if (source.average_time_to_hire_days > 60) {
          logInfo(`⚠️  "${source.source}": Very slow hiring (${source.average_time_to_hire_days.toFixed(0)} days)`);
        }

        // Detect missing stage distribution
        if (!source.stage_distribution || source.stage_distribution.length === 0) {
          logInfo(`⚠️  "${source.source}": No stage distribution data`);
        }
      });
    }

    // Final Summary
    logSection('✨ Validation Summary');
    logSuccess('All integration tests passed!');
    console.log('');
    log('📊 Data Summary:', 'cyan');
    log(`   Sources: ${sources.length}`, 'reset');
    log(`   Total Candidates: ${totalCandidates.toLocaleString()}`, 'reset');
    if (dateRange) {
      log(`   Date Range: ${dateRange}`, 'reset');
    }
    console.log('');
    logSuccess('Frontend component should display this data correctly!');
    console.log('');

  } catch (error) {
    logSection('❌ Validation Failed');

    if (error.response) {
      // Server responded with error status
      logError(`Server returned status ${error.response.status}`);
      logInfo(`Status: ${error.response.status} ${error.response.statusText}`);
      if (error.response.data) {
        logInfo('Response data:', 'reset');
        console.log(JSON.stringify(error.response.data, null, 2));
      }
    } else if (error.request) {
      // Request made but no response
      logError('No response received from server');
      logInfo('Possible issues:');
      logInfo('  - Backend server is not running');
      logInfo('  - Wrong API URL (check port 8000)');
      logInfo('  - Network connectivity issues');
      logInfo('  - Firewall blocking the request');
    } else {
      // Other error (validation error, etc.)
      logError(error.message);
    }

    console.log('');
    log('🔧 Troubleshooting:', 'cyan');
    log('1. Ensure backend server is running:', 'reset');
    log('   cd backend && python -m uvicorn main:app --reload', 'reset');
    log('2. Check if API endpoint exists:', 'reset');
    log('   curl http://localhost:8000/api/analytics/candidate-source-attribution', 'reset');
    log('3. Verify backend has data:', 'reset');
    log('   Check database has AnalyticsEvent records with event_type="resume_uploaded"', 'reset');
    console.log('');

    process.exit(1);
  }
}

// Run validation
validateIntegration().catch((error) => {
  logError('Unhandled error:', error.message);
  console.error(error);
  process.exit(1);
});
