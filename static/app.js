document.getElementById('report-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const days = document.getElementById('days').value;
  const coach = document.getElementById('coach').value;
  const client = document.getElementById('client').value;

  const url = new URL('/getreport', window.location.origin);
  url.searchParams.append('days', days);
  if (coach) url.searchParams.append('coach', coach);
  if (client) url.searchParams.append('client', client);

  document.getElementById('processing').style.display = 'block';

  try {
    const response = await fetch(url);

    if (response.ok) {
      const blob = await response.blob();
      const a = document.createElement('a');
      a.href = window.URL.createObjectURL(blob);
      a.download = `appointments.${coach}.${client}.csv`;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } else {
      alert('Error generating report. Please try again.');
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Error generating report. Please try again.');
  } finally {
    document.getElementById('processing').style.display = 'none';
  }
});
