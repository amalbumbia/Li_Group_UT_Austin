# %%
def hyperspectral_spatial_image(title,folder,calibration_file,xsteps,ysteps,x_step_size,y_step_size,rel_spec_ind,x_crop,y_crop):
    
    # Find and sort all files by number:
    files = [file for file in folder.glob(file_prefix+'*')] # find all relevant files
    files = sorted(files,
                   key=lambda x:float(x.name.replace(file_prefix,'').replace(file_suffix,''))) # sort files by index number

    # Calculate wl from calibration file
    wl = 1240/np.loadtxt(folder/calibration_file)[:,0]
    display(wl)

    # Load all data files into single array
    data_vector = [np.loadtxt(file) for file in files]

    # Rearrange data into spatial map according to preset xsteps and ysteps
    data = np.array(data_vector)
    data=data.reshape(xsteps,ysteps,-1)
    data = data[x_crop[0]: x_crop[1], y_crop[0]:y_crop[1]]
    x_um = np.arange(data.shape[0])*x_step_size
    y_um = np.arange(data.shape[1])*y_step_size

    int_data = data[:,:,rel_spec_ind[0]:rel_spec_ind[1]].sum(axis=2)
    plt.pcolor(int_data,cmap='gray')
    plt.colorbar() 

    # Create Data array in order to define axes 
    data_ds = xr.DataArray(
        data=data,
        coords=dict(

            x=x_um,

            y=y_um,

            wl=wl.round(1),
        ),
        )

    return wl,data_ds,x_um,y_um,data

# %%
def find_peaks(rel_spec_ind,data):
    fig, ax = plt.subplots(1,2)
    rel_data = data[:,:,rel_spec_ind[0]:rel_spec_ind[1]]
    rel_data = ndimage.gaussian_filter(rel_data, sigma=[0.01,0.01,10])

    pts = []

    for i in range(rel_data.shape[2]):
        if np.mod(i,10)==0:
            im = rel_data[:,:, i]
            blobs_doh = blob_dog(im, max_sigma=1, threshold_rel=0.5)
            plt.subplot(1,2,1)
            plt.imshow(im)
            plt.subplot(1,2,2)
            plt.imshow(im)
            for blob in blobs_doh:
                y, x, r = blob
                c = plt.Circle((x, y), r, color='red', linewidth=2, fill=False)
                plt.gca().add_patch(c)
                pts.append([y,x])

            plt.title(wl[rel_spec_ind[0]:rel_spec_ind[1]][i].round(2))
            plt.show()

    unique_pts = np.unique((np.array(pts)).round(), axis=0)
    plt.imshow(data[:,:,rel_spec_ind[0]:rel_spec_ind[1]].sum(axis=2))
    plt.gca().invert_yaxis()
    plt.scatter(unique_pts[:,1],unique_pts[:,0],marker='*',c='r')

    background_spectra = rel_data.sum(axis=0).sum(axis=0)
    # remove peak spectra
    for pt in unique_pts.round().astype(int):
        background_spectra-= rel_data[pt[0], pt[1]]
    # normalize background
    n_points = rel_data.shape[0]*rel_data.shape[1] - len(unique_pts)
    background_spectra /= n_points

    from scipy.cluster.hierarchy import fclusterdata
    cluster_pred = fclusterdata(unique_pts, 1, criterion='distance')
    
    return unique_pts,cluster_pred,background_spectra

# %%
def to_codebook(X, part):
    """
    Calculates centroids according to flat cluster assignment

    Parameters
    ----------
    X : array, (n, d)
        The n original observations with d features

    part : array, (n)
        Partition vector. p[n]=c is the cluster assigned to observation n

    Returns
    -------
    codebook : array, (k, d)
        Returns a k x d codebook with k centroids
    """
    codebook = []

    for i in range(part.min(), part.max()+1):
        codebook.append(X[part == i].mean(0))

    return np.vstack(codebook)

# %%
def label_points(unique_pts,y_um,x_um,rel_spec_ind,title):
    unique_centroids = to_codebook(unique_pts,cluster_pred).round().astype(int)
    plt.pcolor(y_um,
               x_um,
               data[:,:,rel_spec_ind[0]:rel_spec_ind[1]].sum(axis=2),
               cmap='gray'
              )
    plt.xlabel('X (um)')
    plt.ylabel('Y (um)')

    plt.scatter(unique_centroids[:,1]*x_step_size,unique_centroids[:,0]*y_step_size,marker='*',c='b')
    for i in range(len(unique_centroids)):
        plt.annotate(i+1, (unique_centroids[i,1]*x_step_size,unique_centroids[i,0]*y_step_size), c='b')

    #plt.savefig(title + 'spatial_map.png')
    return unique_centroids

# %%
def make_plot(unique_centroids,title,data,wl,background_spectra):

    #fig=go.Figure()

    for i, pt in enumerate(unique_centroids):
        if i == 16: 
            spectrum = data[pt[0]-2:pt[0]+2, pt[1]-2:pt[1]+2].mean(axis=0).mean(axis=0)
            wavelength = wl[rel_spec_ind[0]:rel_spec_ind[1]]
            spectrum = spectrum[:len(wavelength)]
            #wavelength = wavelength[:len(spectrum)]
            #print(f"Spectrum length: {len(spectrum)}, Wavelength length: {len(wavelength)}")
            #fig.add_trace(go.Scatter(x= wl, y =data[pt[0]-2:pt[0]+2,
                                                    #pt[1]-2:pt[1]+2].mean(axis=0).mean(axis=0),
                                    #name=i+1
                                    #'))'
            # Plot spectrum
            plt.figure()
            plt.plot(wavelength, spectrum)
            plt.xlabel('Wavelength (nm)')
            plt.ylabel('PL Intensity')
            plt.title(f'{title} {i+1}')
            plt.grid(False)
            plt.show()
            
            return plt.gca().figure, wavelength, spectrum

    #fig.add_trace(go.Scatter(x=wl[rel_spec_ind[0]:rel_spec_ind[1]], y=background_spectra, name='bkg'))
    #fig.write_html(title + 'spectra_plots.html')
    #fig.show()

# %%
def plot_spectrum(ax, wavelength, spectrum, title, color=None):
    ax.plot(wavelength, spectrum, color=color)
    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('PL Intensity')
    ax.set_title(title)
    ax.grid(False)

# %%
import zipfile as zf
files = zf.ZipFile("spatial_scan.zip", 'r')
files.extractall('spatial_scan')
files.close()

# Define parameters
parent_folder = Path('spatial_scan')
folder = parent_folder / 'spatial_scan'
calibration_file = '2ev_600grating_02052024.asc'
file_prefix = 'Sample1_NCWS2_2ev_5uW_80by75_500nmstep_'
file_suffix = '.dat'
xsteps = 75 #int(np.sqrt(len(files)))
x_step_size = 0.5 # um
ysteps = 80 #int(np.sqrt(len(files)))
y_step_size = 0.5 # um
rel_spec_ind = [130, -1]
x_crop = [0,50]
y_crop = [15,72]
title = 'cryo_mAgNC_'

# %%
def picture(image_path):
    with open(image_path, 'rb') as f:
        image_data = f.read()
    image = mpimg.imread(image_path)
    plt.imshow(image)
    plt.axis('off')
    plt.show()

# %%
def plotting(file, point):
    
    # open file
    with open(file, 'r') as file:
        lines = file.readlines()

    # set range   
    low_wl = 600.0 # nm
    high_wl = 680.0 # nm

    # x and y values
    x = []
    y = []
    for line in lines:
        parts = line.split(',')
        if float(parts[0]) <= low_wl:
            pass
        elif float(parts[0]) >= high_wl:
            pass
        else:
            x.append(float(parts[0])) 
            y.append(float(parts[2]))  

    # Plot
    plt.plot(x, y)
    plt.xlabel('wavelength')  
    plt.ylabel(' ')  
    plt.title(point +' RT mAgNC')  
    plt.grid(False)  
    plt.show()
    # Create a Plotly trace
    trace = go.Scatter(x=x, y=y, mode='lines', name=point + ' RT mAgNC')

    return trace
