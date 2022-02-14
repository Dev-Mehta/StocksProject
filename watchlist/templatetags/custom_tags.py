from django import template

register = template.Library()

def format_indian(t):
	dic = {
		4:'Thousand',
		5:'Lakh',
		6:'Lakh',
		7:'Crore',
		8:'Crore',
		9:'Arab'
	}
	y = 10
	len_of_number = len(str(t))
	save = t
	z=y
	while(t!=0):
		t=int(t/y)
		z*=10

	zeros = len(str(z)) - 3
	if zeros>3:
		if zeros%2!=0:
			string = str(save/(z/100))[0:4]+" "+dic[zeros]
		else:   
			string = str(save/(z/1000))[0:4]+" "+dic[zeros]
		return string
	return str(save)

register.filter('format_indian', format_indian)