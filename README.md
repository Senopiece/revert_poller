## Example usage

1. #### App

    1. (Optionally) Create and enter a venv for the app

    1. Install requirements for the app
        ```
        pip install -r app/requirements.txt
        ```

    1. Run the app
        ```bash
        python3 app --account 0xE69412E799E52aE70ce9df77f56EA019D2e2c7F4 --poll_interval 60
        ```
        > Further can be dockerized or put onto a detached terminal

1. #### Visualize
    1. (Optionally) Create a venv for the ploting script

    1. To visualize charts refer to the [plot script](plot.ipynb).
