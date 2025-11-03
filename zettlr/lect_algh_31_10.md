**Побитовый сдвиги**

`
void bits() {
unsigned char n = 5;
	//cout << (n & 1);
	//cout << ((n >> 1) & 1);
	for (int i = 7; i>=0; i--) {
	cout << ((n >> i) & 1) << ' ';
	}
}
void days () {
	int n;
	cin >> n;
	int day = (n & 7);
	int t = ((n >> 3) & 3);
	switch (t) {
        case 1: cout << "morning "; break;
        case 2: cout << "afternoon "; break;
        case 3: cout << "night "; break;
    }
    switch (day) {
        case 1: cout << "Monday" << endl; break;
        case 2: cout << "Tuesday" << endl; break;
        case 3: cout << "Wednesday" << endl; break;
        case 4: cout << "Thursday" << endl; break;
        case 5: cout << "Friday" << endl; break;
        case 6: cout << "Saturday" << endl; break;
        case 7: cout << "Sunday" << endl; break;
    }
}
void ticket() {
	int n;
	int sum1 = 0, sum2 = 0;
	cin >> n;
	int n1 = n % 1000;
	int n2 = n / 1000;
	while (n1 > 0)
	{
    	sum1 += n % 10;
        n /= 10;
	}
    while (n2 > 0)
    {
    	sum2 += n % 10;
        n /= 10;
    }
    cout << (sum1 == sum2 ? 'yes' : 'no') << endl;
}
int main() {
	return 0;
}
void digit_6 () {
	int n;
	int counter = 0;
	while (n != 0) {
    	if (n % 10 == 6) counter++;
        n /= 10
    }
    cout << (counter >= 2 ? 'yes' : 'no')
}
`

