const fs = require('node:fs');
const assert = require('node:assert/strict');
const html = fs.readFileSync('app/index.html', 'utf8');
const script = html.split('<script>')[1].split('</script>')[0];
function line(prefix) {
  const result = script.split('\n').find((item) => item.startsWith(prefix));
  assert.ok(result, 'Missing JS declaration ' + prefix);
  return result;
}
const source = line('const hm = ') + '\n' + line('const fmtTime = ') + '\nreturn fmtTime;';
const format24 = new Function('S', source)({h24:true});
const format12 = new Function('S', source)({h24:false});
const example = '2026-10-29T16:10:00+10:00';
assert.equal(format24(example), '16:10');
assert.equal(format12(example), '4:10 pm');
assert.equal(format24(null), '');
assert.match(html, /data-time-format="12"/);
assert.match(html, /data-time-format="24"/);
assert.match(html, /S\.h24 = button\.dataset\.timeFormat === '24'/);
console.log('PASS: 12H/24H flight time formatting, colons and user control');
