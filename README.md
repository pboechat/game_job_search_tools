game_job_search_tools
=======

_game_job_search_tools_ is set of Python 3 scripts that scrape the web in search of jobs in the game industry.

It currently features:

 - A CSV generator from the gamedevmap website


----------
### Getting Started

#### 1.  Installing

On Windows:

		./install.bat

On Linux:

		./install.sh


#### 2. Running

##### _gamedevmap_report_


On Windows, open PowerShell and run:

		
		PS C:\game_job_search_tools> .\venv\Scripts\activate.ps1
		(venv) PS C:\game_job_search_tools> gamedevmap_report.exe --country [country] --out [filename]

On Linux, open a terminal and run:

		my_user@my_computer:~/game_job_search_tools/$ ./venv/bin/activate
		(venv) my_user@my_computer:~/game_job_search_tools/$ gamedevmap_report --country [country] --out [filename]


The command line options for _gamedevmap_report_ are:

		usage: gamedevmap_report [-h] 
				--out <filename>
                --country <country_name>
               [--company_type <company_type>]
               [--city <city_name>]
               [--web_scrape_timeout <float>] 

_company_type_ must be one of the following options: 

		Developer
		Developer and Publisher
		Mobile
		Online
		Organization
		Publisher
		Serious Games
		Virtual Reality
